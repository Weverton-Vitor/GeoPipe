from concurrent.futures import ThreadPoolExecutor, as_completed
import glob
import logging
import os
from pathlib import Path
from typing import Any

from tqdm import tqdm

from utils.fmask.Fmask import Fmask
from utils.fmask.fmask_utils import save_mask_tif, save_overlayed_mask_plot
from fmask_pipeline.pipelines.download.nodes import shapefile2feature_collection
from utils.image_reconstuction.strategy import ALGORITHM_REGISTRY, process_single_image
from utils.s2cloudless.gee_s2cloudless import export_s2_cloud_shadow_masks

logger = logging.getLogger(__name__)


def apply_cloud_mask(
    mask_type: str,
    toa_path: str,
    location_name: str,
    save_masks_path: str,
    save_plots_path: str,
    scale: int = 10,
    skip_masks: bool = False,
    *args,
    **kwargs,
):
    if mask_type == 'no_mask':
        logger.warning("Skip generation of cloud and shadow masks")
        return True
    
    if mask_type == "fmask":
        return apply_fmask(
            toa_path=toa_path,
            location_name=location_name,
            save_masks_path=save_masks_path,
            save_plots_path=save_plots_path,
            scale_factor=scale,
            skip_masks=skip_masks,
        )
    elif mask_type == "s2cloudless":
        return apply_s2cloudless(
            shapefile=kwargs.get("shapefile"),
            location_name=location_name,
            save_masks_path=save_masks_path,
            save_plots_path=save_plots_path,
            dowload_path=kwargs.get("dowload_path"),
            init_date=kwargs.get("init_date"),
            final_date=kwargs.get("final_date"),
            prefix_images_name=kwargs.get("prefix_images_name"),
            skip_masks=skip_masks,
            scale=scale,
        )


def apply_fmask(
    toa_path: str,
    location_name: str,
    save_masks_path: str,
    save_plots_path: str,
    scale_factor: int = 10,
    skip_masks: bool = False,
    *args,
    **kwargs,
):
    # TODO REMOVE
    if skip_masks:
        logger.warning("Skip generation of cloud and shadow masks")
        return True

    fmask = Fmask(scale_factor=scale_factor)
    inputs = glob.glob(f"{toa_path}{location_name}/*/*.tif")
    
    for inp in inputs:
        inp = inp.replace("\\", "/")
        file_name = f"{location_name}/fmask/{inp.split('/')[-2]}/mask_{inp.split('/')[-1].split('.')[0]}"

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


def apply_s2cloudless(
    shapefile,
    location_name: str,
    save_masks_path: str,
    save_plots_path: str,
    dowload_path: str,
    init_date: str,
    final_date: str,
    prefix_images_name: str,
    skip_masks: bool = False,
    scale: int = 10,
    *args,
    **kwargs,
):
    if skip_masks:
        logger.warning("Skip generation of cloud and shadow masks")
        return True

    roi_feature_collection = shapefile2feature_collection(shapefile)

    export_s2_cloud_shadow_masks(
        roi_feature_collection=roi_feature_collection,
        location_name=location_name,
        output_dir=f"{save_masks_path}/{location_name}/s2cloudless/",
        save_plots_path=f"{save_plots_path}/{location_name}/s2cloudless/",
        start_date=init_date,
        end_date=final_date,
        scale=scale,
    )

    return True

# TODO refactore to remove coupling
def cloud_removal(
    path_images: str,
    path_masks: str,
    output_path: str,
    location_name: str,
    cloud_and_cloud_shadow_pixels: str,
    init_date: str,
    final_date: str,
    skip_clean: bool,
    color_file_log_path: str,
    cloud_mask_algorithm: str,
    reconstruction_algorithm: str,
    max_workers: int = 4,
    *args: Any,
    **kwargs: Any,
) -> bool:
    """
    Remove clouds from satellite imagery for *location_name* between *init_date*
    and *final_date*.

    Parameters
    ----------
    path_images:
        Root directory that holds per-location / per-year subdirectories of
        GeoTIFF files.
    path_masks:
        Root directory for cloud-mask files produced by *algorithm*.
    output_path:
        Root directory where corrected images are written.
    location_name:
        Reservoir / AOI identifier used to build sub-paths.
    cloud_and_cloud_shadow_pixels:
        Threshold or label string forwarded to the reconstruction strategy.
    init_date:
        First date of the processing window (``"YYYY-MM-DD"``).
    final_date:
        Last date of the processing window (``"YYYY-MM-DD"``).
    skip_clean:
        When *True* the function returns immediately without processing.
    color_file_log_path:
        Root directory for per-year colour-log files.
    reconstruction_algorithm:
        Key into :data:`ALGORITHM_REGISTRY` (default ``"fmask"``).
    max_workers:
        Maximum number of threads used for concurrent image processing.
    """
    if skip_clean or cloud_mask_algorithm == "no_mask":
        logger.warning("Skip Cloud Removal")
        return True

    strategy = ALGORITHM_REGISTRY.get(reconstruction_algorithm)
    if strategy is None:
        raise ValueError(
            f"Unknown algorithm '{reconstruction_algorithm}'. Available: {list(ALGORITHM_REGISTRY)}"
        )

    logger.info(
        "Processing reservoir '%s' with algorithm '%s'.", location_name, reconstruction_algorithm
    )
    

    year_range = range(
        int(init_date.split("-")[0]),
        int(final_date.split("-")[0]) + 1,
    )

    # Count total files upfront for the progress-bar
    all_tifs = glob.glob(os.path.join(path_images, location_name, "**", "*.tif"), recursive=True)
    total_tifs = len(all_tifs)

    extra: dict[str, Any] = kwargs  # forward unknown kwargs to strategies

    with tqdm(total=total_tifs, desc="Cleaning Images", unit="file") as pbar:
        for year in year_range:
            path_images_year = os.path.join(path_images, location_name, str(year), "")
            path_masks_year = os.path.join(
                path_masks, location_name, cloud_mask_algorithm, str(year), ""
            )
            output_path_year = os.path.join(
                output_path, location_name, cloud_mask_algorithm, reconstruction_algorithm, str(year), ""
            )
            color_file_log = os.path.join(
                color_file_log_path, location_name, cloud_mask_algorithm, reconstruction_algorithm, str(year), ""
            )
            # Path(output_path_year).mkdir(parents=True, exist_ok=True)

            tif_files = [f for f in os.listdir(path_images_year) if f.endswith(".tif")]

            if not tif_files:
                logger.debug("No TIF files found for year %d — skipping.", year)
                continue

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(
                        process_single_image,
                        image_filename=fname,
                        year=year,
                        path_images_year=path_images_year,
                        path_masks_year=path_masks_year,
                        output_path_year=output_path_year,
                        color_file_log=color_file_log,
                        location_name=location_name,
                        cloud_pixels=cloud_and_cloud_shadow_pixels,
                        strategy=strategy,
                        extra=extra,
                    ): fname
                    for fname in tif_files
                }

                for future in as_completed(futures):
                    fname = futures[future]
                    try:
                        future.result()
                    except Exception as exc:
                        logger.error("Failed to process '%s': %s", fname, exc)
                    pbar.update(1)

    return True
