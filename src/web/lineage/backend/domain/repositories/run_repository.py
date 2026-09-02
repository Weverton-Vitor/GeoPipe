# domain/repositories/run_repository.py

from abc import ABC, abstractmethod


class RunRepository(ABC):
    @abstractmethod
    def list_runs(self) -> list[str]:
        pass
