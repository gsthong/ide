# Deployment Guide

## Local Deployment (Docker Compose)
Use `docker-compose` to spin up the API and Postgres locally. Since the sandbox uses Docker API via daemon, you must mount the Docker socket into the backend container.

```yaml
version: '3.8'
services:
  backend:
    build: .
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - LLM_PROVIDER=groq
      - GROQ_API_KEY=your_key
    ports:
      - "8000:8000"
      
  db:
      image: postgres:15
      environment:
        - POSTGRES_USER=postgres
```

## Production Deployment (Kubernetes)
For true production environments, avoid DinD (Docker in Docker). Instead, use a specialized sandboxing engine like **gVisor** or **Firecracker**.

1. **Firecracker MicroVMs**: Isolate executions at the kernel level for multi-tenancy.
2. **Kubernetes Jobs**: Use a dedicated worker node pool that handles individual short-lived K8s Pods with gVisor configured via `runtimeClassName: gvisor`.
3. **Queue**: Introduce RabbitMQ caching the analyzer requests, pulling them asynchronously so slow LLMs don't block the API thread pool.
