import contextvars

request_scope = contextvars.ContextVar("request_scope", default=None)

class Scope:
    def __init__(self):
        self.instances: dict[type, object] = {}

    def clear(self):
        self.instances.clear()