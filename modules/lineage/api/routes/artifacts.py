from fastapi import APIRouter, Depends
from api.dependencies import get_artifact_service

router = APIRouter()


@router.get("/{stage}/{run}/{image_id}")
def list_artifacts(
    stage: str,
    run: str,
    image_id: str,
    service=Depends(get_artifact_service),
):
    """
    Lista os artefatos associados a uma imagem.
    """
    artifacts = service.list_artifacts(
        stage=stage,
        run=run,
        image_id=image_id,
    )

    return [
        {
            "name": a.name,
            "type": a.type,
            "stage": a.stage,
            "url": a.path,
        }
        for a in artifacts
    ]
