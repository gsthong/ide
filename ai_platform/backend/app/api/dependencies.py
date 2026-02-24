import os
import redis
from fastapi import Request, HTTPException, Depends
import time

redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/1"))

def get_current_user_id(request: Request) -> int:
    """Mock JWT auth extraction. In Prod, decode PyJWT from headers."""
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer User"):
        # Just returning a mock user 1 for the blueprint
        return 1
    return int(auth.split("User")[1])

def rate_limit(requests_per_minute: int = 10):
    """
    Token bucket style rate limiting utilizing Redis.
    Limits by IP Address.
    """
    def _rate_limit_dependency(request: Request):
        if not redis_client:
            return True
            
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
        # Simple redis counter expiration implementation
        try:
            current = redis_client.get(key)
            if current and int(current) >= requests_per_minute:
                raise HTTPException(status_code=429, detail="Too Many Requests. Submission throttled.")
            else:
                pipe = redis_client.pipeline()
                pipe.incr(key, 1)
                pipe.expire(key, 60)
                pipe.execute()
        except redis.ConnectionError:
            pass # Fail open if redis is down 
            
        return True
    return _rate_limit_dependency

def get_db():
    # Dependency to get AsyncPG session
    yield None
