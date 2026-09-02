from datetime import datetime

from domain.repositories.csv_repository import CsvRepository


class Project:

    def __init__(
        self,
        name: str,
        location: str,
        description: str | None = None,
        shapefile_path: str | None = None,
        elevation_path: str | None = None,
        volume_path: str | None = None,
        id: int | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.id = id
        self.name = name
        self.location = location
        self.description = description
        self.shapefile_path = shapefile_path
        self.elevation_path = elevation_path
        self.volume_path = volume_path
        self.created_at = created_at
        self.updated_at = updated_at
        self.cav = None
        self.real_volumes = None
        self.runs = []
        self.runs_qty = 0
        
        if self.created_at is None:
            self.created_at = datetime.today().date()
        
        if self.updated_at is None:
            self.updated_at = datetime.today().date()

    def __str__(self):
        return (f"{self.name} \n {self.location}")
    
    def read_files(self, repository: CsvRepository = CsvRepository()):
        self.cav = repository.read_elevation(self.elevation_path)
        self.real_volumes = repository.read_real_volumes(self.volume_path)
