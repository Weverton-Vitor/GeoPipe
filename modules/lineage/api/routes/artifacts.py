from fastapi import APIRouter, Depends
from pathlib import Path
from api.dependencies import get_artifact_service

router = APIRouter()


@router.get("/get_artifacts")
def list_artifacts(
    run_name: str,
    day: str,
    year: str,
    month: str,
    service= Depends(get_artifact_service),
):
    """
    Lista os artefatos associados a uma imagem.
    """
    artifacts = service.get_artifacts(run=run_name, day=day, year=year, month=month)

    return {
            a.image_type: {
            "name": a.name,
            "path": a.path,
            "value": a.value,
            } for a in artifacts
        }
