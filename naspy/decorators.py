import functools
import inspect
from typing import  TypeVar
from fastapi import APIRouter, HTTPException, Request
from .guard_middleware import get_global_guards
from .ioc import IoC
from .lifetime_enum import Lifetime
from .use_guards import GUARDS_KEY, SKIP_GUARDS_KEY

class _Injected:
    def __init__(self, type_: type,life_time_: Lifetime = Lifetime.SINGLETON):
        self.type_ = type_
        self.life_time_=life_time_

T = TypeVar('T')
def Injected(type_: T,life_time_: Lifetime = Lifetime.SINGLETON) -> T:
    return _Injected(type_,life_time_)


class _InjectedValue:
    def __init__(self, token: str):
        self.token = token

def InjectedValue(token: str) -> any:
    return _InjectedValue(token)

def Injectable(lifetime: Lifetime = Lifetime.SINGLETON):
    def decorator(cls):
        original_init = cls.__init__ if "__init__" in cls.__dict__ else None

        def __init__(self):
            for klass in type(self).__mro__:
                for attr, value in vars(klass).items():
                    if isinstance(value, _Injected):
                        setattr(self, attr, IoC.resolve(value.type_))
                    elif isinstance(value, _InjectedValue):
                        setattr(self, attr, IoC.resolve_value(value.token))
            if original_init:
                original_init(self)

        cls.__init__ = __init__
        IoC.register(cls, lifetime)  
        return cls
    return decorator

def Controller(prefix: str = "", lifetime: Lifetime = Lifetime.SINGLETON, guards: list = []):
    def decorator(cls):
        cls.__controller_guards__ = guards
        original_init = cls.__init__ if "__init__" in cls.__dict__ else None

        def _wrap_endpoint(func):
            if getattr(func, SKIP_GUARDS_KEY, False):
                return func  

            method_guards = list(getattr(func, GUARDS_KEY, []))
            all_guards = get_global_guards() + cls.__controller_guards__ + method_guards

            @functools.wraps(func)
            async def wrapped(*args, request: Request = None, **kwargs):
                for guard_class in all_guards:
                    guard = IoC.resolve(guard_class)
                    if not await guard.can_activate(request):
                        raise HTTPException(status_code=401, detail="Unauthorized")
                return await func(*args, **kwargs)

            original_sig = inspect.signature(func)
            request_param = inspect.Parameter(
                "request",
                inspect.Parameter.KEYWORD_ONLY,
                annotation=Request,
                default=None
            )
            new_params = list(original_sig.parameters.values()) + [request_param]
            wrapped.__signature__ = original_sig.replace(parameters=new_params)

            return wrapped

        def __init__(self):
            for attr, value in vars(cls).items():
                if isinstance(value, _Injected):
                    setattr(self, attr, IoC.resolve(value.type_))
            if original_init:
                original_init(self)

            self.router = APIRouter(prefix=prefix, tags=[cls.__name__])
            self._wrap_endpoint = _wrap_endpoint

            original_add_api_route = self.router.add_api_route
            def add_api_route_with_guards(path, endpoint, **kwargs):
                wrapped = _wrap_endpoint(endpoint)
                original_add_api_route(path, wrapped, **kwargs)
            self.router.add_api_route = add_api_route_with_guards

            self._register_routes()

        cls.__init__ = __init__
        IoC.register(cls, lifetime)
        return cls

    return decorator