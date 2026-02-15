from domain.repositories.filesystem_artifacts_repository import FileSystemArtifactRepository


class ArtifactsService:
    def __init__(self, artifact_repository: FileSystemArtifactRepository):
        self.artifact_repository = artifact_repository

    def get_artifacts(self, run: str, year: str, month: str, day: str):
        
        artifacts = self.artifact_repository.get_artifacts(run=run, day=day, year=year, month=month)

        return artifacts
    
