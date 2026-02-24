# Security Checklist for Coding Execution

When running arbitrary user code, extreme isolation is required.

- [x] **Disable Network Access:** Run Docker with `network_mode="none"`.
- [x] **Time Limits:** Enforce strict execution time slices (e.g. 5 seconds). Use `container.kill()` aggressively on timeouts.
- [x] **Read-Only RootFS:** Set `read_only=True` to prevent modifying base container files. Only provide `/tmp` via a `tmpfs` volume if strictly needed.
- [x] **Memory Constraints:** Use `mem_limit="128m"` to prevent Out Of Memory (OOM) DOS attacks on the host.
- [x] **CPU Quotas:** `cpu_count=1`.
- [x] **PID Limitations:** `pids_limit=50` to stop malicious fork bombs (`while True: os.fork()`).
- [ ] **Drop Privileges:** Start processes as non-root user (e.g. `user="nobody"`).
- [ ] **Seccomp Profiles:** Apply strict seccomp filtering to block highly dangerous syscalls (`ptrace`, `bpf`, `mount`).
- [ ] **AppArmor/SELinux:** Confine Docker further.
- [ ] **LLM Jailbreak Defenses:** The prompts should be checked before going to the LLM (Prompt Injection prevention via input sanitization).
