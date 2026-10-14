from abc import ABC, abstractmethod


class StoragePort(ABC):
    @abstractmethod
    def put(self, key: str, data: bytes) -> None:
        pass

    @abstractmethod
    def get(self, key: str) -> bytes:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass
