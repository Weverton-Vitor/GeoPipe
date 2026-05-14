from api.dependencies import get_timeseries_service
from domain.services.timeseries_service import TimeSeriesService
from fastapi import APIRouter, Depends, Query

router = APIRouter()


@router.get("/volume")
def get_volume_timeseries(
    service:  TimeSeriesService= Depends(get_timeseries_service),
    run_name: str = Query(alias="run_name"),
    segmentation_method="vggunet",
):
    """
    Retorna a série temporal mensal (média) do volume de água.
    """
    series = service.get_volume(
        run_name=run_name, segmentation_method=segmentation_method
    )

    # Serialização explícita (entidades → JSON)
    return series
