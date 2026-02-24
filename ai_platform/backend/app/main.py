from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from api.routes import submit, auth
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    title="AI Coding Platform API - Production",
    description="A highly scalable, secure, and intelligent coding platform backend.",
    version="1.0.0"
)

# Production CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://play.yourplatform.com", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Mount Routes
app.include_router(auth.router, prefix="/api/v1")
app.include_router(submit.router, prefix="/api/v1")

# Observability (Prometheus)
Instrumentator().instrument(app).expose(app)

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
