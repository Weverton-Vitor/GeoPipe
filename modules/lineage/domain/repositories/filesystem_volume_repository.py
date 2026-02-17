import os
from pathlib import Path
import pandas as pd

from domain.repositories.base import VolumeRepository


class FileSystemVolumeRepository(VolumeRepository):

    def __init__(self, root_path: Path):
        self.root_path = root_path


    def get_volume(self, run_name, segmentation_method):

        results_path = self.root_path / "data/010_areas_volumes"
        comparative_path = self.root_path / "notebooks/data/ana"

        volumes = os.listdir(results_path)
        ana_volumes_path = os.listdir(comparative_path)

        volume = list(
            filter(
                lambda x: run_name in x and segmentation_method in x and "fmask" in x,
                volumes,
            )
        )

        if not volume:
            raise FileNotFoundError("Volume file not found")

        ana_volumes = list(
            filter(
                lambda x: (
                    run_name in x or f"{run_name.replace('_reservatorio', '')}" in x
                ),
                ana_volumes_path,
            )
        )

        # ----------------------------
        # Volume principal
        # ----------------------------
        volume_df = pd.read_csv(results_path / volume[0] / "df_volumes_trh_0.1.csv")

        volume_df["date"] = pd.to_datetime(volume_df[["year", "month", "day"]])
        volume_df = volume_df.sort_values("date")


        # ----------------------------
        # Se não existir ANA → retorna só volume
        # ----------------------------
        if not ana_volumes:
            return {
                "data": volume_df[
                    ["day", "year", "month", "CLOUDY_PIXEL_PERCENTAGE", "volume_m2"]
                ]
            }


        # ----------------------------
        # ANA dataset
        # ----------------------------
        ana_df = pd.read_csv(Path(comparative_path, ana_volumes[0]))

        ana_df = ana_df[["Volume Útil (hm³)", "Data da Medição"]]
        ana_df = ana_df.rename(columns={"Volume Útil (hm³)": "ana_volume"})
        
        # ----------------------------
        # converter volume ANA string -> float
        # ----------------------------
        ana_df["ana_volume"] = (
            ana_df["ana_volume"]
            .astype(str)
            .str.replace(".", "", regex=False)   # remove separador de milhar
            .str.replace(",", ".", regex=False)  # vírgula -> ponto decimal
            .astype(float)
)

        ana_df["date"] = pd.to_datetime(
            ana_df["Data da Medição"], format="%d/%m/%Y"
        )

        ana_df = ana_df.sort_values("date")

        # ----------------------------
        # JOIN TEMPORAL
        # ----------------------------
        merged = pd.merge_asof(
            volume_df,
            ana_df[["date", "ana_volume"]],
            on="date",
            direction="nearest",
            tolerance=pd.Timedelta("30D")  # limite máximo aceitável
        )


        # ----------------------------
        # diferença em dias
        # ----------------------------
        merged["ana_date"] = pd.merge_asof(
            volume_df[["date"]],
            ana_df[["date"]],
            on="date",
            direction="nearest",
            tolerance=pd.Timedelta("30D")
        )["date"]

        merged["days_difference"] = (
            merged["date"] - merged["ana_date"]
        ).dt.days.abs()

        merged["ana_interpolated"] = merged["days_difference"] > 0


        # ----------------------------
        # separa colunas finais
        # ----------------------------
        merged["year"] = merged["date"].dt.year
        merged["month"] = merged["date"].dt.month
        merged["day"] = merged["date"].dt.day

        return {
            "data": merged[
                [
                    "day",
                    "year",
                    "month",
                    "CLOUDY_PIXEL_PERCENTAGE",
                    "volume_m2",
                    "ana_volume",
                    "days_difference",
                    "ana_interpolated",
                ]
            ].to_dict(orient="records")
        }
