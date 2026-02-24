# Production AI Coding Platform Architecture

The architecture has been scaled up heavily to meet true production capabilities:
Scalable, secure, observable, and rate-limited.

```text
ai_platform/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── dependencies.py    # JWT Auth, Rate Limiter (Redis)
│   │   │   ├── routes/
│   │   │   │   ├── submit.py      # Code submission & scoring
│   │   │   │   ├── problems.py    # View problems
│   │   │   │   ├── recommend.py   # Adaptive difficulty logic
│   │   ├── core/
│   │   │   ├── config.py          # Env configuration
│   │   │   ├── celery_app.py      # Background task queue (Celery + Redis)
│   │   │   ├── docker_sandbox.py  # Hardened execution Sandbox (Seccomp, User NS)
│   │   │   ├── security.py        # JWT auth, hashers
│   │   ├── db/
│   │   │   ├── session.py         # AsyncPG connection pool
│   │   │   ├── models.py          # SQLAlchemy PostgreSQL models
│   │   ├── prompts/
│   │   │   ├── analyzer_prompt.py
│   │   ├── schemas/
│   │   │   ├── domain.py          # Pydantic Schemas (API + LLM validation)
│   │   ├── services/
│   │   │   ├── adaptive_engine.py # Skill Elo rating & problem recommendations
│   │   │   ├── llm_service.py     # Fault-tolerant LLM abstraction (Retry, Circuit Breaker, Sanitization)
│   │   │   ├── scoring_engine.py  # Hidden/Public test case evaluation
│   │   ├── main.py                # FastAPI bootstrapper with middleware (CORS, Monitoring)
├── infrastructure/
│   ├── docker-compose.yml         # Local stack (API, Postgres, Redis, Celery, Prometheus)
│   ├── prometheus/                # Observability metrics config
│   ├── k8s/                       # Kubernetes deployment manifests
├── docs/
│   ├── deployment_guide.md        # Prod guide
│   ├── security_checklist.md      # Security checklist
│   ├── frontend_integration.md    # Frontend guides
```

## Data Model Snapshot
* **User & SkillProfile**: Tracks the user Elo rating across problem tags.
* **Problem & Tags**: Manages difficulty, memory/time limits, and tags.
* **Submission & Attempts**: Granular tracking per execution against public & hidden test cases.
* **AIAnalysis**: Caches strict structured JSON feedback to save LLM tokens.

## Event Driven Execution Flow
1. User calls `/submit` -> FastAPI queues task to **Celery**.
2. Celery Worker -> **Hardened Sandbox** pulls code, strictly confines CPU/RAM/Network.
3. Output goes to **Scoring Engine** (evaluates against hidden/public tests).
4. If failed/needs help, **LLM Service** analyzes the error. If JSON is invalid, **Auto-Repair Loop** kicks in.
5. Pushes tracking stats to **Adaptive Engine** for Elo update.
