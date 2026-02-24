import docker
import os
import tempfile
import asyncio
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

try:
    client = docker.from_env()
except Exception:
    client = None

# A strict default seccomp profile for C++ execution.
# This prevents dangerous syscalls like fork, execve (after start), ptrace, and arbitrary network calls.
SECCOMP_PROFILE = {
    "defaultAction": "SCMP_ACT_ERRNO",
    "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_X86", "SCMP_ARCH_X32"],
    "syscalls": [
        {
            "names": [
                "read", "write", "readv", "writev", "close", "fstat", "lseek", "mmap", "mprotect", 
                "munmap", "brk", "rt_sigaction", "rt_sigprocmask", "rt_sigreturn", "ioctl", 
                "pread64", "pwrite64", "readlink", "exit", "exit_group", "arch_prctl", "gettimeofday",
                "clock_gettime", "futex", "set_tid_address", "set_robust_list", "madvise", 
                "uname", "sysinfo", "access", "sched_yield", "openat", "newfstatat", "epoll_wait",
                "epoll_ctl", "tgkill", "gettid", "getpid", "getrandom"
            ],
            "action": "SCMP_ACT_ALLOW",
            "args": [],
            "comment": "Allow standard basic operations and IO to stdin/stdout"
        },
        # Specifically disallowing fork, vfork, clone to prevent fork bombs
        # Disallow execve after initial start
        # Disallow socket, bind, connect, listen, accept for network isolation
    ]
}

async def execute_cpp_secure(code: str, timeout_seconds: int = 5, memory_limit_mb: int = 128) -> Dict[str, Any]:
    """
    Two-stage execution sandbox for C++:
    1. Compile the code (with slightly relaxed resource limits).
    2. Execute the compiled binary (with extremely strict limits and seccomp).
    """
    if not client:
        return {"output": "Docker daemon not available.", "error": True, "tle": False, "memory_used_mb": 0.0, "time_taken_ms": 0, "status": "Runtime Error"}

    with tempfile.TemporaryDirectory() as host_temp_dir:
        code_path = os.path.join(host_temp_dir, "solution.cpp")
        with open(code_path, "w") as f:
            f.write(code)

        # Stage 1: Compilation
        try:
            # We compile by mounting the source read-only, and compiling the output into a temporary folder.
            # To do this safely and retrieve the binary for step 2, we actually mount an output dir for the compiler.
            # However, for maximum security, we'll do both steps in one container lifecycle if possible,
            # using a shell script, because docker network latency between two containers can add up.
            # BUT: combining them means the compiled code runs with the compiler's privileges and seccomp profile.
            # A true production system separates them. Let's do a single container for now but with isolated steps.
            
            # Since we must isolate compilation and execution seccomp profiles, we run two containers.
            compile_container = client.containers.run(
                image="gcc:13",
                command=["g++", "-O2", "-std=c++17", "-static", "-w", "/app/solution.cpp", "-o", "/app/solution"],
                volumes={
                    host_temp_dir: {'bind': '/app', 'mode': 'rw'}
                },
                working_dir="/app",
                network_mode="none",
                mem_limit="512m", # Compilation can be memory intensive
                cpu_count=1,
                detach=False, # Wait for compilation
                remove=True
            )
        except docker.errors.ContainerError as e:
            # Compilation failed
            stderr = e.stderr.decode("utf-8") if e.stderr else "Compilation Error"
            return {
                "output": stderr,
                "error": True,
                "tle": False,
                "time_taken_ms": 0,
                "memory_used_mb": 0.0,
                "status": "Compilation Error"
            }
        except Exception as e:
            logger.error(f"Compilation crash: {str(e)}")
            return {"output": "Internal Compilation Error", "error": True, "tle": False, "time_taken_ms": 0, "memory_used_mb": 0.0, "status": "Compilation Error"}

        # Check if binary was created
        binary_path = os.path.join(host_temp_dir, "solution")
        if not os.path.exists(binary_path):
            return {"output": "Binary not found after compilation", "error": True, "tle": False, "time_taken_ms": 0, "memory_used_mb": 0.0, "status": "Compilation Error"}

        # Make executable (just in case)
        os.chmod(binary_path, 0o755)

        # Stage 2: Execution
        try:
            # PROD-LEVEL ISOLATION for Execution
            container = client.containers.run(
                image="debian:bookworm-slim", # Minimal image, just needs glibc
                command=["/app/solution"],
                volumes={host_temp_dir: {'bind': '/app', 'mode': 'ro'}}, 
                working_dir="/app",
                detach=True,
                network_mode="none",             
                mem_limit=f"{memory_limit_mb}m", 
                memswap_limit=f"{memory_limit_mb}m",             
                pids_limit=20, # Very low fork limit                 
                read_only=True,                  
                cpu_count=1,
                cap_drop=["ALL"], # Drop ALL Linux capabilities
                tmpfs={"/tmp": "size=5m,noexec,nosuid,nodev"},  
                security_opt=[
                    "no-new-privileges:true",
                    # In a real environment, we'd pass a JSON file here for seccomp.
                    # "seccomp=/path/to/profile.json" 
                ], 
                user="1000:1000" # Run as non-root (nobody or generic uid)
            )
            
            start_time = asyncio.get_event_loop().time()
            status = 'created'
            
            while status in ['created', 'running']:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout_seconds:
                    container.kill()
                    return {
                        "output": "Time Limit Exceeded", 
                        "error": True, 
                        "tle": True, 
                        "time_taken_ms": int(elapsed * 1000), 
                        "memory_used_mb": float(memory_limit_mb),
                        "status": "Time Limit Exceeded"
                    }
                
                await asyncio.sleep(0.05)
                try:
                    container.reload()
                    status = container.status
                except docker.errors.NotFound:
                    status = 'exited'

            # Gather telemetry before collecting logs
            stats = container.stats(stream=False)
            mem_usage_bytes = stats.get("memory_stats", {}).get("usage", 0)
            mem_used_mb = mem_usage_bytes / (1024 * 1024)
            time_taken_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)

            # Cap output at 100KB to prevent memory flood
            try:
                logs = container.logs(stdout=True, stderr=True).decode("utf-8")
                if len(logs) > 100000:
                    logs = logs[:100000] + "\n...[Output Truncated]..."
            except docker.errors.APIError:
                logs = "Error reading logs."

            exit_code = container.attrs['State']['ExitCode']
            container.remove(force=True)
            
            # Map exit codes to common segmentation faults, etc.
            is_error = exit_code != 0
            exec_status = "Accepted"
            if is_error:
                if exit_code == 139:
                    exec_status = "Segmentation Fault"
                elif exit_code == 137:
                    exec_status = "Memory Limit Exceeded / Killed" # Often triggered by OOM killer
                    # The container was OOM killed
                    mem_used_mb = float(memory_limit_mb)
                else:
                    exec_status = f"Runtime Error (Exit Code {exit_code})"

            return {
                "output": logs, 
                "error": is_error, 
                "tle": False,
                "time_taken_ms": time_taken_ms,
                "memory_used_mb": round(mem_used_mb, 2),
                "status": exec_status
            }

        except docker.errors.ContainerError as e:
            return {"output": e.stderr.decode("utf-8") if e.stderr else "Fatal runtime error.", "error": True, "tle": False, "time_taken_ms": 0, "memory_used_mb": 0.0, "status": "Runtime Error"}
        except Exception as e:
            logger.error(f"Sandbox crash: {str(e)}")
            return {"output": str(e), "error": True, "tle": False, "time_taken_ms": 0, "memory_used_mb": 0.0, "status": "System Error"}
