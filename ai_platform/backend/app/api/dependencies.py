import os
import redis
from fastapi import Request, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from app.core.config import settings
from app.db.database import get_db_session
from app.db.models import User
from sqlalchemy import select

redis_client = redis.Redis.from_url(settings.REDIS_URL)

async def get_current_user_optional(request: Request, db: AsyncSession = Depends(get_db_session)) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.split(" ")[1]
            
    if not token:
        return None
        
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
        
    result = await db.execute(select(User).where(User.id == int(user_id)))
    return result.scalar_one_or_none()

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db_session)) -> User:
    user = await get_current_user_optional(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user

async def get_current_user_id(user: User = Depends(get_current_user)) -> int:
    return user.id

def rate_limit(requests_per_minute: int = 10):
    async def _rate_limit_dependency(request: Request, user: User | None = Depends(get_current_user_optional)):
        if not redis_client:
            return True
            
        if user:
            identifier = f"user:{user.id}"
        else:
            identifier = f"ip:{request.client.host}"
            
        key = f"rate_limit:{identifier}"
        
        try:
            current = redis_client.get(key)
            if current and int(current) >= requests_per_minute:
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too Many Requests. Submission throttled.")
            else:
                pipe = redis_client.pipeline()
                pipe.incr(key, 1)
                pipe.expire(key, 60)
                pipe.execute()
        except redis.ConnectionError:
            pass # Fail open if redis is down 
            
        return True
    return _rate_limit_dependency

# Export get_db_session as get_db for compatibility with existing routes
get_db = get_db_session
