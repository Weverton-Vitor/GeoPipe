from pathlib import Path
from fastapi import APIRouter, Depends

from api.dependencies import get_images_service
from domain.services.image_service import ImageService

router = APIRouter()


@router.get("/get_for_month")
def list_images_for_month(
    run_name: str,
    year: str,
    month: str,
    service: ImageService = Depends(get_images_service),
):
    """
    Lista imagens de um determinado mês/ano.
    """
    images = service.get_images_for_month(run=run_name, year=year, month=month)

    return {
        "images": [
            {
                "name": img.name,
                "url": f"/static/images/{run_name}/{year}/{month}/{Path(img.png_path).name}"
            }
            for img in images
        ]
    }


@router.get("/get_for_day")
def list_images_for_day(
    run_name: str,
    day: str,
    year: str,
    month: str,
    service: ImageService = Depends(get_images_service),
):
    """
    Lista imagens de um determinado dia/mês/ano.
    """
    images = service.get_images_for_day(run=run_name, day=day, year=year, month=month)

    return {
        "images": [
            {
                "name": img.name,
                "url": f"/static/images/{run_name}/{year}/{month}/{Path(img.png_path).name}"
            }
            for img in images
        ]
    }