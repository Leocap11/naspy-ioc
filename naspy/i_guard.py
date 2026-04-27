from abc import ABC, abstractmethod
from fastapi import Request

class IGuard(ABC):
    @abstractmethod
    async def can_activate(self, request: Request) -> bool:
        ...