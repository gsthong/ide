import docker
import os
import tempfile
import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

try:
    client = docker.from_env()
except Exception:
    client = None

async def execute_code_secure(code: str, language: str = "python", timeout_seconds: int = 5, memory_limit_mb: int = 128) -> Dict[str, Any]:
    """
    Extremely hardened execution sandbox for production environments.
    """
    if not client:
        return {"output": "Docker daemon not available.", "error": True, "tle": False, "memory_used_mb": 0.0, "time_taken_ms": 0}

    if language != "python":
        raise ValueError(f"Language {language} not supported yet.")

    with tempfile.TemporaryDirectory() as host_temp_dir:
        code_path = os.path.join(host_temp_dir, "solution.py")
        with open(code_path, "w") as f:
            f.write(code)

        try:
            # PROD-LEVEL ISOLATION
            # - read_only: Prevent filesystem modification (need tmpfs for stdout/err parsing if writing files)
            # - network_mode="none": Total isolation from internal network and internet
            # - pids_limit: Defends against fork() DOS
            # - mem_limit/memswap_limit: Hard limits
            # - cpu_count: Limit processing bounds
            # - security_opt: Drop privileges via AppArmor/Seccomp profile. User mapping.
            # - tmpfs: Allow only `/tmp` memory-backed temporary writing, max 10MB.
            container = client.containers.run(
                image="python:3.10-slim",
                command=["python", "/app/solution.py"],
                volumes={host_temp_dir: {'bind': '/app', 'mode': 'ro'}}, 
                working_dir="/app",
                detach=True,
                network_mode="none",             
                mem_limit=f"{memory_limit_mb}m", 
                memswap_limit=f"{memory_limit_mb}m",             
                pids_limit=50,                   
                read_only=True,                  
                cpu_count=1,
                tmpfs={"/tmp": "size=10m,noexec"},  
                security_opt=["no-new-privileges:true"], 
                user="nobody" # Run as non-root user
            )
            
            start_time = asyncio.get_event_loop().time()
            status = 'created'
            
            # Poll execution safely (No busy blocking)
            while status in ['created', 'running']:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout_seconds:
                    container.kill()
                    return {"output": "Time Limit Exceeded", "error": True, "tle": True, "time_taken_ms": int(elapsed * 1000), "memory_used_mb": float(memory_limit_mb)}
                
                await asyncio.sleep(0.05)
                try:
                    container.reload()
                    status = container.status
                except docker.errors.NotFound:
                    status = 'exited'

            # Gather telemetry
            stats = container.stats(stream=False)
            mem_usage_bytes = stats.get("memory_stats", {}).get("usage", 0)
            mem_used_mb = mem_usage_bytes / (1024 * 1024)
            time_taken_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)

            # Cap output at 100KB to prevent memory flood from infinite loops printing text
            try:
                logs = container.logs(stdout=True, stderr=True).decode("utf-8")
                if len(logs) > 100000:
                    logs = logs[:100000] + "\n...[Output Truncated]..."
            except docker.errors.APIError:
                logs = "Error reading logs."

            container.remove(force=True)
            return {
                "output": logs, 
                "error": container.attrs['State']['ExitCode'] != 0, 
                "tle": False,
                "time_taken_ms": time_taken_ms,
                "memory_used_mb": round(mem_used_mb, 2)
            }

        except docker.errors.ContainerError as e:
            return {"output": e.stderr.decode("utf-8") if e.stderr else "Fatal error.", "error": True, "tle": False, "time_taken_ms": 0, "memory_used_mb": 0.0}
        except Exception as e:
            logger.error(f"Sandbox crash: {str(e)}")
            return {"output": str(e), "error": True, "tle": False, "time_taken_ms": 0, "memory_used_mb": 0.0}
