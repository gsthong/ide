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

import base64
import uuid

async def compile_cpp_secure(code: str) -> Dict[str, Any]:
    """
    Stage 1: Compile the code inside a container, saving the binary to a Docker-managed Volume.
    This bypasses DooD bind mount path issues.
    """
    if not client:
        return {"output": "Docker daemon not available.", "error": True, "status": "Compilation Error"}

    volume_name = f"cpp_sandbox_{uuid.uuid4().hex}"
    try:
        client.volumes.create(name=volume_name)
    except Exception as e:
        logger.error(f"Volume creation failed: {e}")
        return {"output": "System Error: Volume mapping failed.", "error": True, "status": "Compilation Error"}

    # Base64 encode the code to avoid bash formatting bugs when injecting via shell
    encoded_code = base64.b64encode(code.encode('utf-8')).decode('utf-8')
    compile_script = f"echo {encoded_code} | base64 -d > /app/solution.cpp && g++ -O2 -std=c++17 -static -w /app/solution.cpp -o /app/solution && chmod 755 /app/solution"

    try:
        compile_container = client.containers.run(
            image="gcc:13",
            command=["sh", "-c", compile_script],
            volumes={
                volume_name: {'bind': '/app', 'mode': 'rw'}
            },
            working_dir="/app",
            network_mode="none",
            mem_limit="512m",
            cpu_count=1,
            detach=False,
            remove=True
        )
    except docker.errors.ContainerError as e:
        stderr = e.stderr.decode("utf-8") if e.stderr else "Compilation Error"
        return {
            "output": stderr,
            "error": True,
            "status": "Compilation Error",
            "volume_name": volume_name
        }
    except Exception as e:
        logger.error(f"Compilation crash: {str(e)}")
        return {"output": "Internal Compilation Error", "error": True, "status": "Compilation Error", "volume_name": volume_name}
    
    return {
        "output": "Compilation successful",
        "error": False,
        "status": "Compiled",
        "volume_name": volume_name
    }

async def run_cpp_secure(volume_name: str, stdin_data: str, timeout_seconds: int = 5, memory_limit_mb: int = 128) -> Dict[str, Any]:
    """
    Stage 2: Run the already compiled binary securely with strict seccomp/memory limits.
    """
    if not client:
        return {"output": "Docker missing", "error": True, "tle": False, "memory_used_mb": 0.0, "time_taken_ms": 0, "status": "System Error"}
        
    try:
        # Inject stdin securely by echoing base64 to /tmp/input.txt
        encoded_stdin = base64.b64encode(stdin_data.encode('utf-8')).decode('utf-8')
        run_script = f"echo {encoded_stdin} | base64 -d > /tmp/input.txt && /app/solution < /tmp/input.txt"
        
        # PROD-LEVEL ISOLATION for Execution
        container = client.containers.run(
            image="debian:bookworm-slim",
            command=["sh", "-c", run_script],
            volumes={volume_name: {'bind': '/app', 'mode': 'ro'}}, 
            working_dir="/app",
            detach=True,
            network_mode="none",             
            mem_limit=f"{memory_limit_mb}m", 
            memswap_limit=f"{memory_limit_mb}m",             
            pids_limit=20,                 
            read_only=True,                  
            cpu_count=1,
            cap_drop=["ALL"],
            tmpfs={"/tmp": "size=5m,noexec,nosuid,nodev"},  
            security_opt=[
                "no-new-privileges:true",
            ], 
            user="nobody"
        )
        
        start_time = asyncio.get_event_loop().time()
        status = 'created'
        
        while status in ['created', 'running']:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout_seconds:
                try:
                    container.kill()
                except docker.errors.APIError:
                    pass
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

        stats = container.stats(stream=False)
        mem_usage_bytes = stats.get("memory_stats", {}).get("usage", 0)
        mem_used_mb = mem_usage_bytes / (1024 * 1024)
        time_taken_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)

        # Cap output at 100KB
        try:
            logs = container.logs(stdout=True, stderr=True).decode("utf-8")
            if len(logs) > 100000:
                logs = logs[:100000] + "\n...[Output Truncated]..."
        except docker.errors.APIError:
            logs = "Error reading logs."

        try:
            exit_code = container.attrs['State']['ExitCode']
            container.remove(force=True)
        except Exception:
            exit_code = -1
        
        is_error = exit_code != 0
        exec_status = "Accepted"
        if is_error:
            if exit_code == 139:
                exec_status = "Segmentation Fault"
            elif exit_code == 137:
                exec_status = "Memory Limit Exceeded / Killed"
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

async def cleanup_cpp_secure(volume_name: str):
    """
    Cleans up the docker volume post execution.
    """
    if client and volume_name:
        try:
            vol = client.volumes.get(volume_name)
            vol.remove(force=True)
        except Exception as e:
            logger.warning(f"Failed to cleanup volume {volume_name}: {e}")
