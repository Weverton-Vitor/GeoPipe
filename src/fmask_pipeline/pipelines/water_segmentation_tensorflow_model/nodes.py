import glob
import logging
import os

from tqdm import tqdm

from utils.watnet.watnet_infer import watnet_infer

logger = logging.getLogger(__name__)


def create_dirs(
    water_masks_save_path: str,
    location_name: str,
    init_date: str,
    final_date: str,
    *args,
    **kwargs,
):
    logger.info("Create Water Volume Monitoring pipeline Directories")
    # Create directories structure, if not exists
    os.makedirs(f"{water_masks_save_path}{location_name}/", exist_ok=True)

    for year in range(int(init_date.split("-")[0]), int(final_date.split("-")[0]) + 1):
        os.makedirs(f"{water_masks_save_path}{location_name}/{year}", exist_ok=True)

    return True


def apply_water_segmentation_tensorflow_model(
    tensorflow_model_images_paths: str,
    water_masks_save_path: str,
    location_name: str,
    skip_tensorflow_model,
    model_path,
    patch_size,
    threshold,
    *args,
    **kwargs,
):
    if skip_tensorflow_model:
        logger.warning("Skip Watnet Mask processing")
        return True

    path = f"{tensorflow_model_images_paths}{location_name}"
    tif_files = glob.glob(os.path.join(path, "**", "*.tif"), recursive=True)
    total_tifs = len(tif_files)

    with tqdm(
        total=total_tifs, desc="Segmenting Water in Images", unit="images"
    ) as pbar:
        for path in tif_files:
            tif_path = path.replace("\\", "/")
            watnet_infer(
                image_path=tif_path,
                save_path=f"{water_masks_save_path}{location_name}/{tif_path.split('/')[-2]}/{tif_path.split('/')[-1]}",
                path_model=model_path,
                patch_size=patch_size,
                # threshold=threshold,
            )
            pbar.update(1)

    return True
