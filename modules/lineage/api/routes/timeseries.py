from fastapi import APIRouter, Depends, Query
from api.dependencies import get_timeseries_service
from domain.repositories.filesystem_volume_repository import (
    FileSystemVolumeRepository,
)

router = APIRouter()


@router.get("/volume")
def get_volume_timeseries(
    service: FileSystemVolumeRepository = Depends(get_timeseries_service),
    run_name=Query(alias="run_name"),
    segmentation_method=Query(alias="segmentation_method"),
):
    """
    Retorna a série temporal mensal (média) do volume de água.
    """
    series = service.get_volume(
        run_name=run_name, segmentation_method=segmentation_method
    )

    # Serialização explícita (entidades → JSON)
    return series
