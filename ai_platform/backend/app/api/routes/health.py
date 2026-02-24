from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.database import get_db_session
from app.api.dependencies import redis_client

router = APIRouter(prefix="/health", tags=["monitoring"])

@router.get("/liveness")
async def liveness_probe():
    """
    K8s Liveness Probe: Just checks if the API container is running and responsive.
    """
    return {"status": "alive"}

@router.get("/readiness")
async def readiness_probe(db: AsyncSession = Depends(get_db_session)):
    """
    K8s Readiness Probe: Validates connections to backing services (PostgreSQL, Redis).
    If these are down, the Pod is marked not ready and taken out of the load balancer.
    """
    ready = True
    checks = {
        "database": "down",
        "redis": "down"
    }
    
    # 1. Check DB
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "up"
    except Exception:
        ready = False
        
    # 2. Check Redis
    try:
        if redis_client and redis_client.ping():
            checks["redis"] = "up"
        else:
            ready = False
    except Exception:
        ready = False
        
    if not ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail={"status": "not ready", "checks": checks}
        )
        
    return {"status": "ready", "checks": checks}
