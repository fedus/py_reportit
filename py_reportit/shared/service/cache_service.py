from typing import Optional


class CacheService:

    def __init__(self):
        self.cache = {}

    def set(self, key: str, value: any) -> None:
        self.cache[key] = value

    def unset(self, key: str) -> None:
        if key in self.cache:
            del self.cache[key]

    def get(self, key: str) -> Optional[any]:
        return self.cache.get(key)
