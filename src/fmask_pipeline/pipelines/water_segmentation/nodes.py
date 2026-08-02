import glob
import logging
import os
from itertools import batched

import onnxruntime as ort
import rasterio
import tensorflow as tf
from tqdm import tqdm

from utils.inference.models_register import WATER_SEGMENTATION_MODELS
from utils.watnet.watnet_infer import (
    deepwatermap_infer_onnx,
    watnet_infer_onnx_optimized,
)

logger = logging.getLogger(__name__)

from utils.calculate_spectral_indices import spectral_indices

map_strategies_sentinel = {
    # "EVI": spectral_indices.EVI(),
    "ndvi": spectral_indices.GenericSpectralIndex(7, 3),  # NIR (B8) / RED (B4)
    "ndbi": spectral_indices.GenericSpectralIndex(11, 7),  # SWIR1 (B11) / NIR (B8)
    "ndwi": spectral_indices.GenericSpectralIndex(1, 3),  # GREEN (B3) / NIR (B8)
    "mndwi": spectral_indices.GenericSpectralIndex(1, 4),  # GREEN (B3) / SWIR1 (B11)
}

map_strategies_landsat_8_9 = {
    "evi": spectral_indices.EVI,
    "ndvi": spectral_indices.GenericSpectralIndex(4, 3),  # NIR / RED
    "ndbi": spectral_indices.GenericSpectralIndex(5, 4),  # SWIR1 / NIR
    "ndwi": spectral_indices.GenericSpectralIndex(2, 4),  # GREEN / NIR
    "mndwi": spectral_indices.GenericSpectralIndex(2, 5),  # GREEN / SWIR1
}

map_strategies_landsat_5_7 = {
    "evi": spectral_indices.EVI,
    "ndvi": spectral_indices.GenericSpectralIndex(3, 2),  # NIR / RED
    "ndbi": spectral_indices.GenericSpectralIndex(4, 3),  # SWIR1 / NIR
    "ndwi": spectral_indices.GenericSpectralIndex(1, 3),  # GREEN / NIR
    "mndwi": spectral_indices.GenericSpectralIndex(1, 4),  # GREEN / SWIR1
}


def create_dirs(
    water_masks_save_path: str,
    location_name: str,
    water_model_name: str,
    init_date: str,
    final_date: str,
    cloud_mask_algoritm: str,
    reconstruction_algorithm: str,
    *args,
    **kwargs,
):
    logger.info("Create Water Volume Monitoring pipeline Directories")
    # Create directories structure, if not exists
    model_name = water_model_name.lower()
    path = os.path.join(water_masks_save_path, location_name, "original", model_name)

    if cloud_mask_algoritm != "no_mask":
        path = os.path.join(
            water_masks_save_path,
            location_name,
            cloud_mask_algoritm,
            reconstruction_algorithm,
            model_name,
        )

    os.makedirs(path, exist_ok=True)

    for year in range(int(init_date.split("-")[0]), int(final_date.split("-")[0]) + 1):
        os.makedirs(os.path.join(path, str(year)), exist_ok=True)

    return path


def apply_water_segmentation(
    save_path: str,
    location_name: str,
    skip_water_segmentation: bool,
    water_model_name: str,
    cloud_mask_algoritm: str,
    reconstruction_algorithm: str,
    patch_size: int,
    qty_images_per_batch: int = 20,
    batch_size: int = 32,
    *args,
    **kwargs,
):
    if skip_water_segmentation:
        logger.warning("Skip Water Segmentation processing")
        return True
    
    input_images_paths = "data/04_clean_images/"
    path = os.path.join(
        input_images_paths,
        location_name,
        cloud_mask_algoritm,
        reconstruction_algorithm,
    )
    
    if cloud_mask_algoritm == "no_mask":
        input_images_paths = "data/02_boa_images/"
        path = os.path.join(
            input_images_paths,
            location_name,
        )

    if water_model_name.lower() not in WATER_SEGMENTATION_MODELS:
        logger.error(f"Model {water_model_name} not found in WATER_SEGMENTATION_MODELS")
        return False

    model_path = WATER_SEGMENTATION_MODELS[water_model_name.lower()]["model_path"]

    tif_files = glob.glob(os.path.join(path, "**", "*.tif"), recursive=True)
    total_tifs = len(tif_files)

    if water_model_name.lower() in ["ndwi", "mndwi"]:
        tif_files = glob.glob(os.path.join(path, "**", "*.tif"), recursive=True)
        total_tifs = len(tif_files)

        with tqdm(
            total=total_tifs, desc=f"Calculating Spectral Indices  {water_model_name}", unit="images"
        ) as pbar:
            for tif_path in tif_files:
                tif_path = tif_path.replace("\\", "/")
                output_path = f"{save_path}/{tif_path.split('/')[-2]}/{tif_path.split('/')[-1]}"
                with rasterio.open(tif_path) as src:
                    bands = src.read()
                    setelite_name = tif_path.split("/")[-1].split("_")[2]
                    spectral_strategy_obj = None

                    if setelite_name in ["LC08", "LC09"]:
                        spectral_strategy_obj = map_strategies_landsat_8_9[
                            water_model_name.lower()
                        ]
                    elif setelite_name in ["LC05", "LC07"]:
                        spectral_strategy_obj = map_strategies_landsat_5_7[
                            water_model_name.lower()
                        ]
                    elif setelite_name in ["S2"]:
                        spectral_strategy_obj = map_strategies_sentinel[
                            water_model_name.lower()
                        ]
                    else:
                        logger.error(f"Unknown satellite name: {setelite_name}")
                        continue

                    spectral_indice = spectral_strategy_obj.calculate(bands)
                    profile = src.profile
                    profile.update(
                        count=1, dtype=rasterio.float32
                    )  # Atualize o tipo de dados e o número de bandas
                    with rasterio.open(output_path, "w", **profile) as dst:
                        dst.write(spectral_indice, 1)
                    pbar.update(1)


    else:
        # model = tf.keras.models.load_model(model_path, compile=False)
        # model = ort.InferenceSession(model_path)
        # Tenta usar GPU (CUDA), se não, cai para CPU
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        session = ort.InferenceSession(model_path, providers=providers)

        with tqdm(
            total=total_tifs, desc=f"Segmenting Water in Images with {water_model_name}", unit="images"
        ) as pbar:
            for path_group in batched(tif_files, qty_images_per_batch):
                tif_paths = [path.replace("\\", "/") for path in path_group]

                save_paths = [
                    os.path.join(
                        save_path, tif_path.split("/")[-2], tif_path.split("/")[-1]
                    )
                    for tif_path in tif_paths
                ]
                if "deepwatermap" in model_path:
                    deepwatermap_infer_onnx(
                        image_paths=tif_paths,
                        save_paths=save_paths,
                        ort_session=session,
                        # batch_size=batch_size,
                    )
                else:
                    watnet_infer_onnx_optimized(
                        image_paths=tif_paths,
                        save_paths=save_paths,
                        ort_session=session,
                        patch_size=patch_size,
                        batch_size=batch_size,
                    )

                pbar.update(qty_images_per_batch)

    return True
