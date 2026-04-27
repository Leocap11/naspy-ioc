from starlette.middleware.base import BaseHTTPMiddleware
from .scope_context import request_scope, Scope

class ScopeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        scope = Scope()
        token = request_scope.set(scope) 
        try:
            response = await call_next(request)
        finally:
            scope.clear()
            request_scope.reset(token)  
        return response