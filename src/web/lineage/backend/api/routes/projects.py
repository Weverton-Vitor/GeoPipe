import shutil
from pathlib import Path

from api.dependencies import get_project_service
from domain.entities.project import Project
from domain.schemas.projects import ProjectDetailResponse, ProjectResponse
from domain.services.project_service import ProjectService
from fastapi import APIRouter, Depends, File, Form, Response, UploadFile

router = APIRouter()


@router.get("/", response_model=list[ProjectResponse])
def list_projects(
    service: ProjectService=Depends(get_project_service),
):
    """
    Lista todos os projetos disponíveis.
    """
    return service.get_projects()

@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(
    project_id: int,
    service: ProjectService=Depends(get_project_service),
):
    """
    Busca um projeto específico pelo ID.
    """
    return service.get_project(project_id)


@router.post("/", response_model=ProjectResponse)
def create_project(
    name: str = Form(...),
    location: str = Form(...),
    description: str | None = Form(None),
    shapefile: UploadFile | None = File(None),
    elevation_file: UploadFile | None = File(None),
    volume_file: UploadFile | None = File(None),
    service: ProjectService = Depends(get_project_service),
):
    files_name = location.lower().replace(' ', '_')
    
    # Directories where uploaded files will be stored
    shapefile_dir = Path("D:/GeoPipe/data/00_shapefiles")
    elevation_dir = Path("D:/GeoPipe/data/00_elevation")
    volume_dir = Path("D:/GeoPipe/data/00_real_volumes")

    # Create directories if they don't exist
    shapefile_dir.mkdir(parents=True, exist_ok=True)
    elevation_dir.mkdir(parents=True, exist_ok=True)
    volume_dir.mkdir(parents=True, exist_ok=True)
    
    # Save shapefile
    shapefile_path = None
    if shapefile:
        shapefile_path = shapefile_dir / files_name

        with open(shapefile_path, "wb") as upload_folder:
            shutil.copyfileobj(shapefile.file, upload_folder)

    # Save elevation file
    elevation_path = None
    if elevation_file:
        elevation_path = elevation_dir / files_name

        with open(elevation_path, "wb") as upload_folder:
            shutil.copyfileobj(elevation_file.file, upload_folder)

    # Save volume file
    volume_path = None
    if volume_file:
        volume_path = volume_dir / files_name

        with open(volume_path, "wb") as upload_folder:
            shutil.copyfileobj(volume_file.file, upload_folder)

    # Create project
    project = Project(
        name=name,
        location=location,
        description=description,
        shapefile_path=str(shapefile_path) if shapefile_path else None,
        elevation_path=str(elevation_path) if elevation_path else None,
        volume_path=str(volume_path) if volume_path else None,
    )

    return service.create_project(
        project=project,
    )
