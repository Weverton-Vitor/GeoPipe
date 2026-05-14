from fastapi import APIRouter, Depends
from pathlib import Path
from api.dependencies import get_artifact_service
from domain.services.artifacts_service import ArtifactsService

router = APIRouter()


@router.get("/get_artifacts")
def list_artifacts(
    run_name: str,
    day: str,
    year: str,
    month: str,
    service: ArtifactsService = Depends(get_artifact_service),
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

@router.get("/get_water_mask")
def get_water_mask(
    run_name: str,
    day: str,
    year: str,
    month: str,
    threshold: float = 0.5,
    service: ArtifactsService = Depends(get_artifact_service),
):
    """
    Retorna o conteúdo binário de um artefato específico.
    """
    return service.get_water_mask(run=run_name, day=day, year=year, month=month, threshold=threshold)
