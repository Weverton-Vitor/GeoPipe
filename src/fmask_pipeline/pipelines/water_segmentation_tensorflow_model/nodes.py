import glob
import logging
import os

import tensorflow as tf
from tqdm import tqdm
from itertools import batched

from utils.watnet.watnet_infer import (
    watnet_infer,
    watnet_infer_batch,
    watnet_infer_onnx_optimized,
    deepwatermap_infer_onnx,
)
import onnxruntime as ort

logger = logging.getLogger(__name__)


def create_dirs(
    water_masks_save_path: str,
    location_name: str,
    use_no_cloud_images: bool,
    model_path: str,
    init_date: str,
    final_date: str,
    cloud_mask_algoritm: str,
    reconstruction_algorithm: str,
    *args,
    **kwargs,
):
    logger.info("Create Water Volume Monitoring pipeline Directories")
    # Create directories structure, if not exists
    model_name = model_path.split("/")[-1].split(".")[0]
    path = os.path.join(
        water_masks_save_path, location_name, "original", model_name
    )
    if use_no_cloud_images:
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


def apply_water_segmentation_tensorflow_model(
    tensorflow_model_images_paths: str,
    save_path: str,
    location_name: str,
    skip_tensorflow_model,
    model_path,
    patch_size,
    qty_images_per_batch=20,
    batch_size=32,
    *args,
    **kwargs,
):
    if skip_tensorflow_model:
        logger.warning("Skip Watnet Mask processing")
        return True

    path = f"{tensorflow_model_images_paths}{location_name}"
    tif_files = glob.glob(os.path.join(path, "**", "*.tif"), recursive=True)
    total_tifs = len(tif_files)

    # model = tf.keras.models.load_model(model_path, compile=False)
    # model = ort.InferenceSession(model_path)
    # Tenta usar GPU (CUDA), se não, cai para CPU
    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    session = ort.InferenceSession(model_path, providers=providers)

    with tqdm(
        total=total_tifs, desc="Segmenting Water in Images", unit="images"
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
