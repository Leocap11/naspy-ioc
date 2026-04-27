# NasPy 🐍


<p align="center">
  <img src="https://raw.githubusercontent.com/Leocap11/naspy-ioc/main/assets/naspy-logo.png" width="160"/>
</p>

<h1 align="center">NasPy 🐍</h1>

<p align="center">
  NestJS-inspired IoC container for FastAPI
</p>

<p align="center">
  <img src="https://img.shields.io/pypi/v/naspy-ioc.svg">
  <img src="https://img.shields.io/badge/python-3.12+-blue.svg">
  <img src="https://img.shields.io/badge/license-MIT-green.svg">
</p>

**NasPy** is a NestJS-inspired IoC (Inversion of Control) container and decorator library for FastAPI. It brings familiar patterns like `@Injectable`, `@Controller`, `@UseGuards`, dependency injection, and lifecycle management to Python.

---

## Installation

```bash
pip install naspy
```

---

## Quick Start

```python
from naspy import Injectable, Controller, Injected, IoC, Lifetime
from fastapi import FastAPI

@Injectable()
class GreetingService:
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"

@Controller("/hello")
class HelloController:
    greetingService = Injected(GreetingService)

    def _register_routes(self):
        self.router.add_api_route("/{name}", self.get_hello, methods=["GET"])

    async def get_hello(self, name: str):
        return self.greetingService.greet(name)

app = FastAPI()
app.include_router(IoC.resolve(HelloController).router)
```

---

## Project Structure

NasPy is opinionated — here is the recommended project structure:

```
app/
├── main.py
├── .env
├── core/
│   └── app_module.py
├── domain/
│   └── user/
│       ├── usecase/
│       │   └── get_user/
│       │       ├── get_user_command.py
│       │       └── get_user_usecase.py
│       └── model/
│           └── user_model.py
├── repository/
│   └── user/
│       ├── user_repository.py
│       └── user_schema.py
├── controller/
│   └── user/
│       ├── user_controller.py
│       └── user_dto.py
└── guards/
    └── auth_guard.py
```

---

## Configuration

NasPy provides a base `NaspySettings` class built on top of `pydantic-settings`. It automatically reads from your `.env` file.

### `.env`

```dotenv
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/mydb
ENVIRONMENT=development
```

### Extending Settings

```python
from naspy.config import NaspySettings

class Settings(NaspySettings):
    SECRET_KEY: str
    DEBUG: bool = False

settings = Settings()
```

`NaspySettings` provides two required fields out of the box:

| Field | Type | Required |
|---|---|---|
| `DATABASE_URL` | `str` | ✅ |
| `ENVIRONMENT` | `str` | ✅ |

---

## Database

NasPy provides a `Database` class and a `BaseRepository` for PostgreSQL using SQLAlchemy async.

### Setup

Register the `AsyncEngine` factory in your module:

```python
# app/core/app_module.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from naspy import IoC, Lifetime
from app.core.settings import settings

class AppModule:
    def register():
        IoC.register_factory(
            AsyncEngine,
            lambda: create_async_engine(settings.DATABASE_URL, echo=True),
            Lifetime.SINGLETON
        )
```

### `Database`

NasPy exports `Database` and `Base` (SQLAlchemy `DeclarativeBase`) directly:

```python
from naspy.database import Database, Base
```

`Database` is a singleton that holds the `async_sessionmaker`. It is injected automatically into `BaseRepository`.

### Defining a Schema

```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String
from naspy.database import Base

class UserSchema(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True)
```

---

## BaseRepository

`BaseRepository` provides CRUD operations out of the box. Extend it and set the `model` attribute.

```python
from naspy.database import BaseRepository
from naspy import Injectable
from app.repository.user.user_schema import UserSchema

@Injectable()
class UserRepository(BaseRepository[UserSchema]):
    model = UserSchema
```

### Available methods

| Method | Signature | Description |
|---|---|---|
| `find_all` | `() -> list[T]` | Returns all records |
| `find_by_id` | `(id: int) -> T or None` | Returns a single record by id |
| `save` | `(entity: T) -> T` | Inserts or updates a record |
| `delete` | `(id: int) -> bool` | Deletes a record by id |

Each method opens its own session from the connection pool and closes it automatically — no manual session management needed.

```python
@Injectable()
class GetUserUseCase:
    repository = Injected(UserRepository)

    async def run(self, id: int):
        return await self.repository.find_by_id(id)
```

---

## Core Concepts

### `@Injectable`

Marks a class as injectable and registers it in the IoC container.

```python
@Injectable()
class MyService:
    def do_something(self):
        return "done"
```

Supports all three lifetimes:

```python
@Injectable()                        # SINGLETON (default)
@Injectable(Lifetime.SINGLETON)      # one instance for the entire app lifetime
@Injectable(Lifetime.SCOPED)         # one instance per request
@Injectable(Lifetime.TRANSIENT)      # new instance every time it is resolved
```

| Lifetime | NestJS equivalent | Behavior |
|---|---|---|
| `Lifetime.SINGLETON` | `Scope.DEFAULT` | One instance for the entire app lifetime |
| `Lifetime.SCOPED` | `Scope.REQUEST` | New instance per request, shared within the same request |
| `Lifetime.TRANSIENT` | `Scope.TRANSIENT` | New instance every time it is resolved |

---

### `@Controller`

Registers a class as a controller and sets up an `APIRouter`.

```python
@Controller("/users")
class UserController:

    def _register_routes(self):
        self.router.add_api_route("", self.get_all, methods=["GET"])
        self.router.add_api_route("/{id}", self.get_by_id, methods=["GET"])

    async def get_all(self):
        ...

    async def get_by_id(self, id: int):
        ...
```

Register the router in your FastAPI app:

```python
app.include_router(IoC.resolve(UserController).router)
```

---

### `Injected`

Marks a class attribute as an injectable dependency.

```python
@Injectable()
class UserService:
    repository = Injected(UserRepository)

    async def find(self, id: int):
        return await self.repository.find_by_id(id)
```

---

### `InjectedValue`

Injects a registered value (non-class) by token.

```python
# registration
IoC.register_value("MAX_RETRIES", 3)
IoC.register_value("SUPPORTED_CURRENCIES", ["USD", "EUR", "GBP"])

# injection
@Injectable()
class PaymentService:
    max_retries = InjectedValue("MAX_RETRIES")
    currencies = InjectedValue("SUPPORTED_CURRENCIES")
```

---

### `IoC`

The IoC container. Manages registration and resolution of dependencies.

```python
# register a factory
IoC.register_factory(IMailService, lambda: MailService(), Lifetime.SINGLETON)

# register a value
IoC.register_value("CONFIG", {"timeout": 30})

# resolve a dependency
service = IoC.resolve(MyService)

# resolve a value
config = IoC.resolve_value("CONFIG")
```

---

### Factory providers

Equivalent to NestJS `useFactory` — useful for conditional or dynamic instantiation:

```python
class AppModule:
    def register():
        IoC.register_factory(
            IMailService,
            lambda: IoC.resolve(MailService) if os.getenv("ENVIRONMENT") == "production"
                    else IoC.resolve(FakeMailService),
            Lifetime.SINGLETON
        )
```

Call `register()` before creating the FastAPI app:

```python
AppModule.register()
app = create_app()
```

---

### Guards

Guards control access to routes, equivalent to NestJS `@UseGuards`.

#### Define a guard

```python
from naspy import IGuard, Injectable
from fastapi import Request

@Injectable()
class AuthGuard(IGuard):
    async def can_activate(self, request: Request) -> bool:
        token = request.headers.get("Authorization")
        return token is not None
```

#### Apply guards at different levels

```python
from naspy import UseGuards, SkipGuards, set_global_guards

# 1. Global — applies to all routes in the app
set_global_guards(AuthGuard)

# 2. Controller — applies to all routes in the controller
@Controller("/users", guards=[AuthGuard])
class UserController:
    ...

# 3. Method — applies to a single route
@UseGuards(RolesGuard)
async def get_by_id(self, id: int):
    ...

# 4. Skip all guards on a specific route
@SkipGuards()
async def get_public(self):
    ...
```

Guard resolution priority:

```
Global guards
    └── Controller guards
            ├── @SkipGuards    → skip all guards
            ├── @UseGuards     → global + controller + method guards
            └── (no decorator) → global + controller guards
```

---

### Exception Filters

Register a global exception filter to standardize all error responses:

```python
from naspy import register_exception_filters

def create_app() -> FastAPI:
    app = FastAPI()
    register_exception_filters(app)
    ...
```

All errors will follow this format:

```json
{
    "outcome": false,
    "error": {
        "code": 401,
        "status": "Unauthorized",
        "message": "Invalid or missing token"
    }
}
```

---

### Scoped Middleware

Add `ScopeMiddleware` to enable `Lifetime.SCOPED` dependencies:

```python
from naspy import ScopeMiddleware

def create_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(ScopeMiddleware)
    ...
```

Scoped dependencies must be resolved inside request methods using `IoC.resolve()`:

```python
async def get_by_id(self, id: int):
    logger = IoC.resolve(RequestLogger)  # new instance per request
    logger.log(f"Fetching id={id}")
    ...
```

---

## Full Example

```python
# main.py
from fastapi import FastAPI
from naspy import IoC, set_global_guards, register_exception_filters, ScopeMiddleware
from app.guards.auth_guard import AuthGuard
from app.controller.user.user_controller import UserController
from app.core.app_module import AppModule

def create_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(ScopeMiddleware)
    register_exception_filters(app)
    set_global_guards(AuthGuard)
    app.include_router(IoC.resolve(UserController).router)
    return app

AppModule.register()
app = create_app()
```

```python
# app/core/app_module.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from naspy import IoC, Lifetime
from naspy.config import NaspySettings

class Settings(NaspySettings):
    SECRET_KEY: str

settings = Settings()

class AppModule:
    def register():
        IoC.register_factory(
            AsyncEngine,
            lambda: create_async_engine(settings.DATABASE_URL, echo=True),
            Lifetime.SINGLETON
        )
```

```python
# app/repository/user/user_schema.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String
from naspy.database import Base

class UserSchema(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True)
```

```python
# app/repository/user/user_repository.py
from naspy import Injectable
from naspy.database import BaseRepository
from app.repository.user.user_schema import UserSchema

@Injectable()
class UserRepository(BaseRepository[UserSchema]):
    model = UserSchema
```

```python
# app/domain/user/usecase/get_user/get_user_usecase.py
from naspy import Injectable, Injected
from app.repository.user.user_repository import UserRepository

@Injectable()
class GetUserUseCase:
    repository = Injected(UserRepository)

    async def run(self, id: int):
        return await self.repository.find_by_id(id)
```

```python
# app/controller/user/user_controller.py
from naspy import Controller, Injected, SkipGuards
from app.domain.user.usecase.get_user.get_user_usecase import GetUserUseCase

@Controller("/users")
class UserController:
    getUserUseCase = Injected(GetUserUseCase)

    def _register_routes(self):
        self.router.add_api_route("/public", self.get_public, methods=["GET"])
        self.router.add_api_route("/{id}", self.get_by_id, methods=["GET"])

    @SkipGuards()
    async def get_public(self):
        return {"public": True}

    async def get_by_id(self, id: int):
        return await self.getUserUseCase.run(id)
```

---

## Comparison with NestJS

| NestJS | NasPy |
|---|---|
| `@Injectable()` | `@Injectable()` |
| `@Controller('/path')` | `@Controller('/path')` |
| `@UseGuards(Guard)` | `@UseGuards(Guard)` |
| `app.useGlobalGuards()` | `set_global_guards(Guard)` |
| `Scope.DEFAULT` | `Lifetime.SINGLETON` |
| `Scope.REQUEST` | `Lifetime.SCOPED` |
| `Scope.TRANSIENT` | `Lifetime.TRANSIENT` |
| `useFactory` | `IoC.register_factory()` |
| `useValue` | `IoC.register_value()` |
| `AppModule` | `AppModule.register()` |
| `ModuleRef.resolve()` | `IoC.resolve()` |
| `TypeOrmModule` | `BaseRepository` |
| `ConfigService` | `NaspySettings` |

---

## Requirements

- Python >= 3.12
- FastAPI >= 0.100.0
- SQLAlchemy >= 2.0.0
- Starlette >= 0.27.0
- Pydantic >= 2.0.0
- pydantic-settings >= 2.0.0
- asyncpg >= 0.27.0

---

## License

MIT