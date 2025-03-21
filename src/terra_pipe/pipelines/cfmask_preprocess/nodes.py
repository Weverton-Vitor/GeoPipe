"""
This is a boilerplate pipeline 'cfmask_preprocess'
generated using Kedro 0.19.10
"""

import gc
import glob
import logging

from tqdm import tqdm

from utils.cfmask.cfmask_utils import get_binary_mask_from_path
from utils.fmask.fmask_utils import save_mask_tif, save_overlayed_mask_plot

logger = logging.getLogger(__name__)


def apply_cfmask(
    boa_path: str,
    location_name: str,
    save_masks_path: str,
    save_plots_path: str,
    scale_factor: int = 1,
    skip_masks: bool = False,
    *args,
    **kwargs,
):
    if skip_masks:
        logger.warning("Skip generation of cloud and shadow masks")
        return True

    inputs = glob.glob(f"{boa_path}{location_name}/*/*.tif")
    with tqdm(
        total=len(inputs),
        desc="Segmenting Cloud and Cloud Shadows in Images",
        unit="images",
    ) as pbar:
        for image in inputs:
            image_input = image.replace("\\", "/")
            file_name = f"{location_name}/{image_input.split('/')[-2]}/mask_{image_input.split('/')[-1].split('.')[0]}"

            masks = get_binary_mask_from_path(image_path=image_input)
            cloud_mask = masks["cloud_mask"]
            shadow_mask = masks["shadow_cloud_mask"]
            water_mask = masks["water_mask"]
            rgb_composite = masks["rgb_composite"]

            save_overlayed_mask_plot(
                color_composite=rgb_composite,
                masks=[cloud_mask, shadow_mask, water_mask],
                output_file=f"{save_plots_path}{file_name}.png",
            )

            save_mask_tif(
                cloud_mask=cloud_mask,
                cloud_shadow_mask=shadow_mask,
                water_mask=water_mask,
                original_tif_file=image_input,
                output_file=f"{save_masks_path}{file_name}.tif",
            )
            pbar.update(1)

            del masks
            del cloud_mask
            del shadow_mask
            del water_mask
            del rgb_composite

            gc.collect()

    return True
