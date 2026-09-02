from datetime import date
from pydantic import BaseModel, ConfigDict


class ProjectResponse(BaseModel):
    id: int
    name: str
    location: str
    description: str | None = None
    shapefile_path: str | None = None
    elevation_path: str | None = None
    volume_path: str | None = None
    runs_qty: int = 0
    updated_at: date

    model_config = ConfigDict(from_attributes=True)
    
    
class ProjectDetailResponse(BaseModel):
    id: int
    name: str
    location: str
    description: str | None

    shapefile_path: str | None
    elevation_path: str | None
    volume_path: str | None

    cav: list[dict]
    real_volumes: list[dict]
    runs: list[dict]

    updated_at: date