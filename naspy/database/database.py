from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from ..decorators import Injectable
from ..config.settings import settings

class Base(DeclarativeBase):
    pass

@Injectable()
class Database:
    def __init__(self):
        self._engine = create_async_engine(settings.DATABASE_URL, echo=True)
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    def get_session_factory(self) -> async_sessionmaker:
        return self._session_factory