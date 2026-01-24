from functools import wraps
from fastapi import Request, Response
from redis_cache import redis_cache
import json

def cache(ttl: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                raise Exception("Request object not found in arguments")

            user_id = kwargs.get("user_id")
            if not user_id:
                raise Exception("user_id not found in arguments")

            key = f"portfolio:{user_id}"
            cached_response = await redis_cache.get(key)

            if cached_response:
                return json.loads(cached_response)

            response = await func(*args, **kwargs)
            await redis_cache.set(key, json.dumps(response), ttl=ttl)
            return response
        return wrapper
    return decorator
