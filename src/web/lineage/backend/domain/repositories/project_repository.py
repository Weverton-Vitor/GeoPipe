# domain/repositories/run_repository.py

from abc import ABC, abstractmethod

from domain.entities.project import Project


class ProjectRepository(ABC):
    @abstractmethod
    def list_projects(self) -> list[Project]:
        pass

    @abstractmethod
    def get_project(self, project_id) -> Project:
        pass

    @abstractmethod
    def create_project(self, project) -> list[str]:
        pass
