# Security & Abuse Prevention Checklist

Security forms the core tenant of running a platform that allows untrusted code execution combined with costly LLM models.

## Infrastructure Security
- [x] **Rate Limiting (Redis):** Throttling applied via dependency injection (`api/dependencies.py` to prevent DDOS and bot brute forcing). Max 15 req/min.
- [x] **Cost / LLM Throttling:** The AI analysis is deferred to a background queue, allowing you to scale workers dynamically without locking the main REST threads.
- [x] **Docker Kernel Isolation:** `pids_limit`, `memswap_limit`, `cpu_count` restricted preventing forks and memory leaks entirely. No network bridges.
- [x] **Non-Root Runtime:** Sandboxes execute under the `nobody` user.
- [x] **Read-Only Root Filesystem:** Executions mount standard libraries Read-Only.

## API & Data Security
- [x] **Input Size Cap:** Pydantic strictly rejects files/code exceeding 50,000 characters preventing storage bloating.
- [x] **Strict Pydantic Validation on LLM Output:** Guards against prompt injections manipulating the returned structure. A continuous loop repairs schema defects.
- [x] **CORS Constraints:** Restricted origins configured in `main.py`.

## Future Scaling Security (Production K8s)
- [ ] Migrate from Docker DinD to **gVisor** runtime classes in Kubernetes. Docker's daemon is vulnerable if the host node is compromised. gVisor replaces the kernel entirely for the Pod.
- [ ] Implement WAF (Cloudflare) for edge caching and geographic rate limiting.
- [ ] Apply stricter Seccomp profiles blocking `ptrace`, `bpf`, `unshare`.
