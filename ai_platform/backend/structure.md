# Backend Project Structure

The modern FastAPI application uses a layered clean architecture. 

```text
backend/
├── app/
│   ├── api/                  # API routing
│   │   ├── dependencies.py   # common FastAPI dependencies (DB, LLM client)
│   │   ├── routes/           # specific endpoints
│   │   │   ├── analyze.py    # AI code analysis route
│   │   │   ├── execute.py    # Code execution route
│   ├── core/                 # Core utilities
│   │   ├── config.py         # App configuration (Pydantic BaseSettings)
│   │   ├── docker_sandbox.py # Secure Docker execution engine
│   ├── db/                   # Database logic
│   │   ├── models.py         # SQLAlchemy models (User, Progress, Problem)
│   │   ├── session.py        # AsyncPG / SQLAlchemy engine setup
│   ├── prompts/              # LLM System Prompts & Templates
│   │   ├── analyzer_prompt.py
│   ├── schemas/              # Pydantic validation schemas
│   │   ├── analysis.py
│   │   ├── execution.py
│   ├── services/             # Application services
│   │   ├── llm_service.py    # Abstraction layer for LLM (Groq, Together, Ollama)
│   ├── main.py               # FastAPI App definition
├── pyproject.toml            # Poetry/uv dependency management
├── Dockerfile                # API runner
├── Dockerfile.sandbox        # Sandbox runner
```

**Design Decisions:**
- **Clean Architecture:** Separating routes (API layer), business logic (Services layer), and isolation logic (Core).
- **Scalability:** The `docker_sandbox.py` acts as a lightweight wrapper, but execution can easily be offloaded to a queue (e.g., Celery/RabbitMQ) when scaling.
