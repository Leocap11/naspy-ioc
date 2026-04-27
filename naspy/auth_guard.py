# app/guards/auth_guard.py
from fastapi import Request
from .i_guard import IGuard
from .decorators import Injectable

@Injectable()
class AuthGuard(IGuard):
    async def can_activate(self, request: Request) -> bool:
        token = request.headers.get("Authorization")
        if not token:
            return False
        return True