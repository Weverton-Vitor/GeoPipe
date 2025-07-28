import glob
import logging
import os

import numpy as np
from tqdm import tqdm

import utils.deepwatermap.inference as deep_water_map
from utils.watnet.utils.geotif_io import readTiff, writeTiff
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


def apply_watnet(
    images_path: str,
    water_masks_save_path: str,
    location_name: str,
    skip_watnet,
    threshold,
    *args,
    **kwargs,
):
    if skip_watnet:
        logger.warning("Skip Watnet Mask processing")
        return True

    path = f"{images_path}{location_name}"
    tif_files = glob.glob(os.path.join(path, "**", "*.tif"), recursive=True)
    total_tifs = len(tif_files)

    with tqdm(
        total=total_tifs, desc="Segmenting Water in Images", unit="images"
    ) as pbar:
        for path in tif_files:
            tif_path = path.replace("\\", "/")
            #watnet_infer(
               # image_path=tif_path,
              #  save_path=f"{water_masks_save_path}{location_name}/{tif_path.split('/')[-2]}/{tif_path.split('/')[-1]}",
             #   threshold=threshold,
            #)

            sen2_img, img_info = readTiff(path_in=tif_path)
            sen2_img = np.float32(
                np.clip(sen2_img / 10000, a_min=0, a_max=1)
            )  ## normalization
            ## surface water mapping by using watnet
            water_map = watnet_infer(rsimg=sen2_img)
            # write out the result
            writeTiff(
                im_data=water_map.astype(np.int8),
                im_geotrans=img_info["geotrans"],
                im_geosrs=img_info["geosrs"],
                path_out=f"{water_masks_save_path}{location_name}/{tif_path.split('/')[-2]}/{tif_path.split('/')[-1]}",
            )
            pbar.update(1)

    return True
