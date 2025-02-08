import glob
import logging
import os

import rasterio as TIFF
from tqdm import tqdm

from utils.cloud_removal.bcl import BCL
from utils.fmask.Fmask import Fmask
from utils.fmask.fmask_utils import save_mask_tif, save_overlayed_mask_plot

logger = logging.getLogger(__name__)


def apply_fmask(
    toa_path: str,
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

    fmask = Fmask(scale_factor=scale_factor)
    inputs = glob.glob(f"{toa_path}{location_name}/*/*.tif")

    for inp in inputs:
        inp = inp.replace("\\", "/")
        file_name = f"{location_name}/{inp.split('/')[-2]}/mask_{inp.split('/')[-1].split('.')[0]}"

        color_composite, cloud_mask, shadow_mask, water_mask = fmask.create_fmask(inp)

        save_overlayed_mask_plot(
            [cloud_mask, shadow_mask, water_mask],
            color_composite,
            output_file=f"{save_plots_path}{file_name}.png",
        )

        save_mask_tif(
            cloud_mask=cloud_mask,
            cloud_shadow_mask=shadow_mask,
            water_mask=water_mask,
            original_tif_file=inp,
            output_file=f"{save_masks_path}{file_name}.tif",
        )

    return True


def cloud_removal(
    path_images: str,
    path_masks: str,
    output_path: str,
    location_name: str,
    cloud_and_cloud_shadow_pixels: str,
    init_date: str,
    final_date: str,
    skip_clean: bool,
    *args,
    **kwargs,
):
    if skip_clean:
        logger.warning("Skip Cloud Removal")
        return True

    logger.info(f"Executando reservatório {location_name}.")

    year_range = range(int(init_date.split("-")[0]), int(final_date.split("-")[0]) + 1)

    tif_files = glob.glob(os.path.join(path_images, "**", "*.tif"), recursive=True)
    total_tifs = len(tif_files)

    with tqdm(total=total_tifs, desc="Cleaning Images", unit="file") as pbar:
        for year in year_range:
            path_images_year = f"{path_images}{location_name}/{year}/"
            path_masks_year = f"{path_masks}{location_name}/{year}/"

            for image in os.listdir(path_images_year):
                # Greping img_size limits
                with TIFF.open(path_images_year + image) as tiff:
                    image_tiff = tiff.read()

                size = image_tiff.shape[1], image_tiff.shape[2]

                # obtenção da data
                date = image.split("_")[-1].split(".")[0].replace("-", "")

                # logger.info(f"Image shape: {image_tiff.shape} | Image date: {date}")

                # Classe que será utilizada
                i = BCL(
                    img_dim=size,
                    scl_path=path_masks_year,
                    path_6B=path_images_year,
                    year=year,
                    data=date,
                    intern_reservoir=location_name,
                    cloud_pixels=cloud_and_cloud_shadow_pixels,
                    use_dec_tree=False,
                )

                # Correção
                try:
                    i.singleImageCorrection(
                        date,
                        year,
                        f"{output_path}{location_name}/{year}/",
                        image.replace(".tif", ""),
                    )
                except Exception as e:
                    logger.error(e)
                    continue

                pbar.update(1)
                # cv2.imwrite(output_path + f"mask_{image}.png", i.mask)
                i.death()

    return True
