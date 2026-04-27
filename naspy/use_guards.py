from fastapi import HTTPException, Request
from ioc import IoC

GUARDS_KEY = "__guards__"
SKIP_GUARDS_KEY = "__skip_guards__"

def UseGuards(*guards):
    def decorator(func):
        async def wrapper(self, *args, request: Request = None, **kwargs):
            all_guards = (
                getattr(self, "__global_guards__", []) +
                getattr(self.__class__, "__controller_guards__", []) +
                list(guards)
            )
            for guard_class in all_guards:
                guard = IoC.resolve(guard_class)
                if not await guard.can_activate(request):
                    raise HTTPException(status_code=401, detail="Unauthorized")
            return await func(self, *args, **kwargs)
        wrapper.__name__ = func.__name__
        setattr(wrapper, GUARDS_KEY, guards)
        return wrapper
    return decorator

def SkipGuards():
    """Exclude a route from controller and global guards."""
    def decorator(func):
        setattr(func, SKIP_GUARDS_KEY, True)
        return func
    return decorator