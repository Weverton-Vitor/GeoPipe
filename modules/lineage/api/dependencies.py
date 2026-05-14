from pathlib import Path

from config import LINEAGE_ROOT
from domain.repositories.file_system_run_repository import (
    FileSystemRunRepository,
)
from domain.repositories.filesystem_images_repository import (
    FileSystemImageRepository,
)
from domain.repositories.filesystem_volume_repository import (
    FileSystemVolumeRepository,
)
from domain.services.artifacts_service import ArtifactsService
from domain.services.image_service import ImageService
from domain.services.runs_service import RunService
from domain.services.timeseries_service import TimeSeriesService
from fastapi import Depends

from domain.repositories.filesystem_artifacts_repository import (
    FileSystemArtifactRepository,
)


def get_images_service():
    image_repo = FileSystemImageRepository(Path(LINEAGE_ROOT))
    return ImageService(image_repo)


def get_timeseries_service():
    volume_repo = FileSystemVolumeRepository(Path(LINEAGE_ROOT))
    return TimeSeriesService(volume_repository=volume_repo)  # placeholder


def get_run_service():
    return RunService(run_repository=FileSystemRunRepository(Path(LINEAGE_ROOT)))


def get_artifact_service():
    return ArtifactsService(
        artifact_repository=FileSystemArtifactRepository(Path(LINEAGE_ROOT))
    )
