from fastapi import APIRouter, Depends
from api.dependencies import get_run_service

router = APIRouter()


@router.get("/")
def list_runs(service=Depends(get_run_service)):
    """
    Lista todas as etapas e runs disponíveis.
    """
    return service.get_runs()
