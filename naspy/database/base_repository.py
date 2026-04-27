from typing import Generic, TypeVar, Type
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from .database import Database, Base 
from ..ioc import IoC


T = TypeVar("T", bound=Base)

class BaseRepository(Generic[T]):
    model: Type[T]

    def __init__(self):
        db: Database = IoC.resolve(Database)
        self._session_factory: async_sessionmaker = db.get_session_factory()

    async def find_all(self) -> list[T]:
        async with self._session_factory() as session:
            result = await session.execute(select(self.model))
            return result.scalars().all()

    async def find_by_unique_id(self, id: str) -> T | None:
        async with self._session_factory() as session:
            result = await session.execute(select(self.model).where(self.model.id == id))
            return result.scalar_one_or_none()

    async def save(self, entity: T) -> T:
        async with self._session_factory() as session:
            session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return entity

    async def update_entity(self, id: str, data: T) -> T:
        async with self._session_factory() as session:
            result = await session.execute(
                select(self.model).where(self.model.id == id)
            )
            entity = result.scalar_one_or_none()
            if entity is None:
                raise Exception("Entity not found")
            
            for attribute, value in vars(data).items():
                if not attribute.startswith('_') and value is not None and hasattr(entity, attribute):
                    setattr(entity, attribute, value)
            
            session.add(entity) 
            await session.commit()
            await session.refresh(entity)
            return entity

    async def delete(self, id: str) -> bool:
        async with self._session_factory() as session:
            entity = await self.find_by_unique_id(id)
            if not entity:
                return False
            await session.delete(entity)
            await session.commit()
            return True