import glob
import logging
import os

import rasterio
from tqdm import tqdm

import utils.deepwatermap.inference as deep_water_map
from utils.calculate_spectral_indices import spectral_indices 

map_strategies_sentinel = {
    # "EVI": spectral_indices.EVI(),
    "NDVI": spectral_indices.GenericSpectralIndex(7, 3),   # NIR (B8) / RED (B4)
    "NDBI": spectral_indices.GenericSpectralIndex(11, 7),  # SWIR1 (B11) / NIR (B8)
    "NDWI": spectral_indices.GenericSpectralIndex(2, 7),   # GREEN (B3) / NIR (B8)
    "MNDWI": spectral_indices.GenericSpectralIndex(2, 11), # GREEN (B3) / SWIR1 (B11)
}

map_strategies_landsat_8_9 = {
    "EVI": spectral_indices.EVI,
    "NDVI": spectral_indices.GenericSpectralIndex(4, 3),    # NIR / RED
    "NDBI": spectral_indices.GenericSpectralIndex(5, 4),    # SWIR1 / NIR
    "NDWI": spectral_indices.GenericSpectralIndex(2, 4),    # GREEN / NIR
    "MNDWI": spectral_indices.GenericSpectralIndex(2, 5),   # GREEN / SWIR1
}

map_strategies_landsat_5_7 = {
    "EVI": spectral_indices.EVI,
    "NDVI": spectral_indices.GenericSpectralIndex(3, 2),    # NIR / RED
    "NDBI": spectral_indices.GenericSpectralIndex(4, 3),    # SWIR1 / NIR
    "NDWI": spectral_indices.GenericSpectralIndex(1, 3),    # GREEN / NIR
    "MNDWI": spectral_indices.GenericSpectralIndex(1, 4),   # GREEN / SWIR1
}



logger = logging.getLogger(__name__)




def create_dirs(
    spectral_indice: str,
    spectral_index_save_path: str,
    location_name: str,
    init_date: str,
    final_date: str,
    *args,
    **kwargs,
):
    logger.info("Create Spectral Indices Pipeline Directories")
    # Create directories structure, if not exists
    os.makedirs(f"{spectral_index_save_path}{location_name}/{spectral_indice}", exist_ok=True)

    for year in range(int(init_date.split("-")[0]), int(final_date.split("-")[0]) + 1):
        os.makedirs(f"{spectral_index_save_path}{location_name}/{year}/{spectral_indice}", exist_ok=True)

    return True


def calculate_spectral_indices(
    images_path: str,
    spectral_index_save_path: str,
    location_name: str,
    spectral_indice_name,
    skip_spectral_indice,
    *args,
    **kwargs,
):
    if skip_spectral_indice:
        logger.warning("Skip Spectral Indices processing")
        return True

    path = f"{images_path}{location_name}"
    tif_files = glob.glob(os.path.join(path, "**", "*.tif"), recursive=True)
    total_tifs = len(tif_files)

    with tqdm(
        total=total_tifs, desc="Calculating Spectral Indices", unit="images"
    ) as pbar:
        for tif_path in tif_files:
            tif_path = tif_path.replace("\\", "/")
            output_path = f"{spectral_index_save_path}{location_name}/{tif_path.split('/')[-2]}/{spectral_indice_name}/{tif_path.split('/')[-1].replace('.tif', f'_{spectral_indice_name}.tif')}"
            with rasterio.open(tif_path) as src:
                bands = src.read()
                setelite_name = tif_path.split("/")[-1].split("_")[3]
                spectral_strategy_obj = None

                if setelite_name in ["LC08", "LC09"]:
                    spectral_strategy_obj = map_strategies_landsat_8_9[spectral_indice_name]
                elif setelite_name in ["LC05", "LC07"]:
                    spectral_strategy_obj = map_strategies_landsat_5_7[spectral_indice_name]
                elif setelite_name in ["S2"]:
                    spectral_strategy_obj = map_strategies_sentinel[spectral_indice_name]
                else:
                    logger.error(f"Unknown satellite name: {setelite_name}")
                    continue

                spectral_indice = spectral_strategy_obj.calculate(bands)
                profile = src.profile
                profile.update(
                    count=1,
                    dtype=rasterio.float32
                )  # Atualize o tipo de dados e o número de bandas
                with rasterio.open(output_path, "w", **profile) as dst:
                    dst.write(spectral_indice, 1)
                pbar.update(1)

    return True