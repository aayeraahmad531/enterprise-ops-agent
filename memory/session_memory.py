"""
A tiny in-memory session/memory store. ADK offers pluggable SessionService/MemoryBank;
this is a minimal local imitation for demos.
"""
import threading

class InMemorySession:
    def __init__(self):
        self.store = {}
        self.lock = threading.Lock()

    def write(self, key, value):
        with self.lock:
            self.store[key] = value

    def read(self, key, default=None):
        with self.lock:
            return self.store.get(key, default)

    def all(self):
        with self.lock:
            return dict(self.store)
