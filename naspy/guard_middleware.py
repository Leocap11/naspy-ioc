from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
from .ioc import IoC

_global_guards = []

def set_global_guards(*guards):
    global _global_guards
    _global_guards = list(guards)

def get_global_guards():
    return _global_guards

class GlobalGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        for guard_class in _global_guards:
            guard = IoC.resolve(guard_class)
            if not await guard.can_activate(request):
                raise HTTPException(status_code=401, detail="Unauthorized")
        return await call_next(request)