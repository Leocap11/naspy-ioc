from typing import get_type_hints, Type, TypeVar,Callable
from lifetime_enum import Lifetime
from scope_context import request_scope

T = TypeVar("T")

class IoC:
    _registry: dict[type, tuple[type, Lifetime]] = {}
    _instances: dict[type, object] = {}
    _factories: dict[type, Callable] = {}
    _values: dict[str, any] = {}


    @classmethod
    def register(cls, klass: type, lifetime: Lifetime = Lifetime.SINGLETON):
        cls._registry[klass] = (klass, lifetime)
        
    @classmethod
    def register_factory(
        cls,
        klass: Type[T],
        factory: Callable[[], T],
        lifetime: Lifetime = Lifetime.SINGLETON
    ) -> None:
        cls._factories[klass] = (factory, lifetime)
        
        
    @classmethod
    def register_value(cls, token: str, value: any) -> None:
        cls._values[token] = value

    @classmethod
    def resolve_value(cls, token: str) -> any:
        if token not in cls._values:
            raise Exception(f"No value registered for token '{token}'")
        return cls._values[token]


    @classmethod
    def _create_instance(cls, klass: type, _resolving: set):
        print(f"🆕 Creating: {klass.__name__}")

        hints = get_type_hints(klass.__init__) if "__init__" in klass.__dict__ else {}

        deps = {
            name: cls.resolve(dep, _resolving)
            for name, dep in hints.items()
            if name != "return"
        }

        return klass(**deps)

    @classmethod
    def resolve(cls, klass: Type[T], _resolving: set = None) -> T:
        scope = request_scope.get()

        if _resolving is None:
            _resolving = set()

        # circular dependency check
        if klass in _resolving:
            chain = " -> ".join(k.__name__ for k in _resolving)
            raise Exception(f"Circular dependency detected: {chain} -> {klass.__name__}")

        _resolving.add(klass)

        factory_entry = cls._factories.get(klass)

        if factory_entry:
            factory, lifetime = factory_entry
            instance = factory()

            if lifetime == Lifetime.SINGLETON:
                cls._instances[klass] = instance

            elif lifetime == Lifetime.REQUEST:
                if scope is None:
                    raise Exception("Request scope not available")
                scope.instances[klass] = instance

            _resolving.remove(klass)
            return instance

        # -------------------------------------------------------
        # 2️⃣ REGISTRY RESOLUTION (interface → implementation)
        # -------------------------------------------------------
        registry_entry = cls._registry.get(klass)

        if registry_entry is None:
            impl = klass
            lifetime = Lifetime.SINGLETON
        else:
            impl, lifetime = registry_entry

        # -------------------------------------------------------
        # 3️⃣ REQUEST LIFETIME
        # -------------------------------------------------------
        if lifetime == Lifetime.REQUEST:
            if scope is None:
                raise Exception("Request scope not available")

            if impl in scope.instances:
                _resolving.remove(klass)
                return scope.instances[impl]

            instance = cls._create_instance(impl, _resolving)
            scope.instances[impl] = instance

            _resolving.remove(klass)
            return instance

        # -------------------------------------------------------
        # 4️⃣ SINGLETON LIFETIME
        # -------------------------------------------------------
        if lifetime == Lifetime.SINGLETON:
            if impl in cls._instances:
                _resolving.remove(klass)
                return cls._instances[impl]

            instance = cls._create_instance(impl, _resolving)
            cls._instances[impl] = instance

            _resolving.remove(klass)
            return instance

        # -------------------------------------------------------
        # 5️⃣ TRANSIENT (default)
        # -------------------------------------------------------
        instance = cls._create_instance(impl, _resolving)

        _resolving.remove(klass)
        return instance