from domain.entities.project import Project
from domain.repositories.project_repository import ProjectRepository
from infrastructure.database.sqlite.database import SessionLocal
from infrastructure.database.sqlite.models.project_model import ProjectModel


class ProjectRepositorySqlite(ProjectRepository):
    def list_projects(self) -> list[Project]:
        with SessionLocal() as session:
            projects = session.query(ProjectModel).all()

            return [
                self._to_entity(project)
                for project in projects
            ]

    def get_project(self, project_id: int) -> Project | None:
        with SessionLocal() as session:
            project = (
                session.query(ProjectModel)
                .filter(ProjectModel.id == project_id)
                .first()
            )

            if project is None:
                return None

            return self._to_entity(project)

    def create_project(self, project: Project) -> Project:
        with SessionLocal() as session:
            db_project = ProjectModel(
                name=project.name,
                location=project.location,
                description=project.description,
                shapefile_path=project.shapefile_path,
                elevation_path=project.elevation_path,
                volume_path=project.volume_path,
            )

            session.add(db_project)
            session.commit()
            session.refresh(db_project)

            project.id = db_project.id

            return project
        
    def _to_entity(self, project: ProjectModel) -> Project:
        return Project(
            id=project.id,
            name=project.name,
            location=project.location,
            description=project.description,
            shapefile_path=str(project.shapefile_path).replace("\\", "/"),
            elevation_path=str(project.elevation_path).replace("\\", "/"),
            volume_path=str(project.volume_path).replace("\\", "/"),
        )
