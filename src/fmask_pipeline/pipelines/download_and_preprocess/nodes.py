import datetime
import glob
import logging
import os

import ee
import geojson
import geopandas as gpd
import rasterio as TIFF
import requests
from tqdm import tqdm

from utils.cloud_removal.bcl import BCL
from utils.fmask.Fmask import Fmask
from utils.fmask.fmask_utils import save_mask_tif, save_overlayed_mask_plot

# Obter o logger específico do node
logger = logging.getLogger(__name__)


def create_dirs(
    toa_dowload_path: str,
    boa_dowload_path: str,
    location_name: str,
    save_masks_path: str,
    save_plots_path: str,
    save_clean_images_path: str,
    init_date: str,
    final_date: str,
):
    logger.info("Create Download and Preprocess Pipeline Directories")
    # Create directories structure, if not exists
    os.makedirs(f"{toa_dowload_path}{location_name}/", exist_ok=True)
    os.makedirs(f"{boa_dowload_path}{location_name}/", exist_ok=True)
    os.makedirs(f"{save_masks_path}{location_name}/", exist_ok=True)
    os.makedirs(f"{save_plots_path}{location_name}/", exist_ok=True)

    for year in range(int(init_date.split("-")[0]), int(final_date.split("-")[0]) + 1):
        os.makedirs(f"{toa_dowload_path}{location_name}/{year}", exist_ok=True)
        os.makedirs(f"{boa_dowload_path}{location_name}/{year}", exist_ok=True)
        os.makedirs(f"{save_masks_path}{location_name}/{year}", exist_ok=True)
        os.makedirs(f"{save_plots_path}{location_name}/{year}", exist_ok=True)
        os.makedirs(f"{save_clean_images_path}{location_name}/{year}", exist_ok=True)

    return True


def shapefile2feature_collection(
    shapefile: gpd.GeoDataFrame, *args, **kwargs
) -> ee.FeatureCollection:
    # Convert from GeoDataFrame to GeoJson
    geojson_data = geojson.loads(shapefile.to_json())

    # Create the FeatureCollection from geojson
    fc = ee.FeatureCollection(geojson_data)

    return fc


def donwload_images(
    collection_ids: str,
    location_name: str,
    dowload_path: str,
    init_date: str,
    final_date: str,
    roi: ee.FeatureCollection,
    prefix_images_name: str,
    selected_bands: list = [],
    skip_download: bool = False,
    scale: int = 10,
) -> bool:
    if skip_download:
        logger.warning("Skip Download of images")
        return True

    for collection_id in collection_ids:
        # Get collection
        collection = (
            ee.ImageCollection(collection_id)
            .filterDate(init_date, final_date)
            .filterBounds(roi)
        )

        min_date = collection.aggregate_min("system:time_start")
        max_date = collection.aggregate_max("system:time_start")

        min_date = ee.Date(min_date).format("YYYY-MM-dd").getInfo()
        max_date = ee.Date(max_date).format("YYYY-MM-dd").getInfo()

        logger.info(f"Donwload: {collection_id} collection")
        logger.info(f"Collection Date Availability: {min_date} - {max_date}")

        if not selected_bands:
            logger.warning("Download All Bands")
        else:
            logger.warning(f"Download Bands: {selected_bands}")

        logger.info(f"Total images: {collection.size().getInfo()}")

        images = collection.toList(collection.size()).getInfo()

        for i, image_info in enumerate(
            tqdm(images, desc="Downloading Images", unit="imagem")
        ):
            image_id = image_info["id"]
            image = ee.Image(image_id)

            # Filter if necessary
            if selected_bands:
                image = image.select(selected_bands)

            url = image.getDownloadURL(
                {
                    "scale": scale,  # Resolução espacial
                    "region": roi.geometry(),  # Região de interesse
                    "crs": "EPSG:4326",  # Sistema de coordenadas
                    "format": "GeoTIFF",  # Formato de saída
                }
            )

            # Get date of image
            timestamp = image_info["properties"]["system:time_start"]  # Timestamp Unix
            date = datetime.datetime.utcfromtimestamp(timestamp / 1000).strftime(
                "%Y-%m-%d"
            )  # Converte para data legível

            # Nome do arquivo de saída
            output_file = os.path.join(
                f"{dowload_path}{location_name}/{date[:4]}",
                f"{prefix_images_name}_{location_name}_{date}.tif",
            )

            # Faz o download da imagem e salva no diretório especificado
            response = requests.get(url)
            with open(output_file, "wb") as file:
                file.write(response.content)

    return True


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
