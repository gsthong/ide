import docker
import os
import tempfile
import asyncio

try:
    client = docker.from_env()
except Exception:
    client = None

async def execute_code(code: str, language: str = "python", timeout_seconds: int = 5) -> dict:
    """
    Executes student code using Docker with extreme restrictions:
    - Custom PIDs limit (prevent fork bombs)
    - Memory & CPU limits
    - Read-only file system (except for strict temp dir)
    - Network isolation
    """
    if not client:
        return {"output": "Docker daemon not available.", "error": True, "tle": False}

    if language != "python":
        raise ValueError(f"Language {language} not supported yet.")

    # Create a temporary directory mapping
    with tempfile.TemporaryDirectory() as host_temp_dir:
        code_path = os.path.join(host_temp_dir, "solution.py")
        with open(code_path, "w") as f:
            f.write(code)

        try:
            # Run container detached to enforce async timeout
            container = client.containers.run(
                image="python:3.10-slim",
                command=["python", "/app/solution.py"],
                volumes={host_temp_dir: {'bind': '/app', 'mode': 'ro'}}, 
                working_dir="/app",
                detach=True,
                network_mode="none",             # No network access
                mem_limit="128m",                # Small memory limit to prevent OOM DOS
                pids_limit=50,                   # Prevent fork bombs
                read_only=True,                  # Read only rootfs
                cpu_count=1                      # Restrict to single CPU
            )
            
            # Start timer loop
            start_time = asyncio.get_event_loop().time()
            status = 'created'
            
            while status in ['created', 'running']:
                if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                    container.kill()
                    return {"output": "Time Limit Exceeded", "error": True, "tle": True}
                
                await asyncio.sleep(0.1)
                container.reload()
                status = container.status

            logs = container.logs().decode("utf-8")
            container.remove()
            return {"output": logs, "error": False, "tle": False}

        except docker.errors.ContainerError as e:
            return {"output": e.stderr.decode("utf-8"), "error": True, "tle": False}
        except Exception as e:
            return {"output": str(e), "error": True, "tle": False}
