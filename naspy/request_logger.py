from datetime import datetime
from .decorators import Injectable
from .lifetime_enum import Lifetime

@Injectable(Lifetime.REQUEST)
class RequestLogger:
    def __init__(self):
        self.created_at = datetime.now()
        print(f"📋 RequestLogger created at {self.created_at}")

    def log(self, message: str):
        print(f"[{self.created_at}] {message}")