from collections import defaultdict
from datetime import date
from domain.repositories.base import VolumeRepository


class TimeSeriesService:
    def __init__(self, volume_repository: VolumeRepository):
        self.volume_repository = volume_repository

    def get_volume(self, run_name: str, segmentation_method: str):
        volumes_df = self.volume_repository.get_volume(
            run_name=run_name, segmentation_method=segmentation_method
        )

        return volumes_df.to_dict(orient="list")
