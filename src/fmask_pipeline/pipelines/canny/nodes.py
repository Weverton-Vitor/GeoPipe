import glob
import logging
import os

from tqdm import tqdm

from utils.coastline import canny

logger = logging.getLogger(__name__)


def create_dirs(
    canny_output_save_path: str,
    location_name: str,
    init_date: str,
    final_date: str,
    *args,
    **kwargs,
):
    logger.info("Create Coastline pipeline Directories")
    # Create directories structure, if not exists
    os.makedirs(f"{canny_output_save_path}{location_name}/", exist_ok=True)

    for year in range(int(init_date.split("-")[0]), int(final_date.split("-")[0]) + 1):
        os.makedirs(f"{canny_output_save_path}{location_name}/{year}", exist_ok=True)

    return True


def apply_canny(
    images_path: str,
    canny_output_save_path: str,
    location_name: str,
    *args,
    **kwargs,
):
    path = f"{images_path}{location_name}"
    tif_files = glob.glob(os.path.join(path, "**", "*.tif"), recursive=True)
    total_tifs = len(tif_files)
    canny_detector = canny.Canny()

    with tqdm(
        total=total_tifs, desc="Generating CostLine using Canny Method", unit="images"
    ) as pbar:
        for tif_path in tif_files:
            output_path = f"{canny_output_save_path}{location_name}/{tif_path.split('/')[-2]}/{tif_path.split('/')[-1].replace('.tif', '_canny.tif')}"
            canny_detector.detect_border(tif_path=tif_path, output_path=output_path)
            pbar.update(1)

    return True
