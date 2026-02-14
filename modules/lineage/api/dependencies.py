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
from domain.services.image_service import ImageService
from domain.services.runs_service import RunService
from domain.services.timeseries_service import TimeSeriesService
from fastapi import Depends

# futuramente:
# from domain.repositories.volume import FileSystemVolumeRepository


def get_images_service():
    image_repo = FileSystemImageRepository(Path(LINEAGE_ROOT))
    return ImageService(image_repo)


def get_timeseries_service():
    volume_repo = FileSystemVolumeRepository(Path(LINEAGE_ROOT))
    return TimeSeriesService(volume_repository=volume_repo)  # placeholder


def get_run_service():
    # implementar depois
    return RunService(run_repository=FileSystemRunRepository(Path(LINEAGE_ROOT)))


def get_artifact_service():
    # implementar depois
    raise NotImplementedError
