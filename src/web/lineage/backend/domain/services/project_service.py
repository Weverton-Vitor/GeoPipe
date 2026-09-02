from domain.repositories.project_repository import ProjectRepository
from domain.entities.project import Project


class ProjectService:
    """
    Serviço de domínio responsável por regras relacionadas às runs.
    """

    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    def get_projects(self) -> list[Project]:
        """
        Retorna a lista de runs disponíveis para uma etapa do pipeline.
        """

        project = self.project_repository.list_projects()
        return project

    def get_project(self, project_id) -> Project:
        """
        Retorna a lista de runs disponíveis para uma etapa do pipeline.
        """

        project = self.project_repository.get_project(project_id)
        project.read_files()
        
        return project

    def create_project(
        self,
        project: Project,
    ):

        return self.project_repository.create_project(project)
