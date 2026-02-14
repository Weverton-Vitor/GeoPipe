import os
from pathlib import Path

import pandas as pd

from domain.entities.image import ImageBOA
from domain.repositories.base import VolumeRepository


class FileSystemVolumeRepository(VolumeRepository):
    def __init__(self, root_path: Path) -> pd.DataFrame:
        self.root_path = root_path

    def get_volume(self, run_name, segmentation_method):
        results_path = self.root_path / "data/010_areas_volumes"
        comparative_path = results_path / "notebooks/data"

        volumes = os.listdir(results_path)
        # ana_volumes = os.listdir(comparative_path)

        volume = list(
            filter(
                lambda x: run_name in x and segmentation_method in x and "fmask" in x,
                volumes,
            )
        )

        # ana_volumes = list(
        #     filter(
        #         lambda x: run_name in x,
        #         ana_volumes,
        #     )
        # )

        volume_df = pd.read_csv(results_path / volume[0] / "df_volumes_trh_0.1.csv")
        # ana_volumes_df = pd.read_csv(ana_volumes[0])
        # ana_volumes_df = ana_volumes_df["Volume (%)", "Data da Medição"]
        # ana_volumes_df["year"] = pd.to_datetime(ana_volumes_df["Data da Medição"]).dt.year
        # ana_volumes_df["month"] = pd.to_datetime(ana_volumes_df["Data da Medição"]).dt.month
        # ana_volumes_df['day'] = pd.to_datetime(ana_volumes_df["Data da Medição"]).dt.day

        return volume_df[["day", "year", "month", "CLOUDY_PIXEL_PERCENTAGE", "volume_m2"]]
