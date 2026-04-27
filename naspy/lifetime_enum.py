from enum import Enum

class Lifetime(Enum):
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    REQUEST = "request"