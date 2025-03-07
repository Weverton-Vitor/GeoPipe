import datetime
import glob
import logging
import os
from datetime import datetime

import ee
import geojson
import geopandas as gpd
import rasterio as TIFF
import requests
from tqdm import tqdm

from utils.download.download import (
    adjust_date,
    get_original_bands_name,
    is_TOA,
    validate_date,
)

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
    collection_ids: list,
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
        # Validando as datas
        satelite_name = collection_id.split("/")[1]

        if "S2" in satelite_name:
            satelite_name = "S2"

        new_init_date, new_final_date = adjust_date(
            satelite=satelite_name, start_date_str=init_date, end_date_str=final_date
        )

        logger.warning(
            f"A data inicial para o satelite {satelite_name} foi alterada para {new_init_date}"
        )
        logger.warning(
            f"A data final para o satelite {satelite_name} foi alterada para {new_final_date}"
        )

        validate_date(satelite=satelite_name, date_str=new_init_date)
        validate_date(satelite=satelite_name, date_str=new_final_date)

        if new_final_date == new_init_date:
            logger.warning(
                "Data inicial e final iguais, passando para a próxima coleção"
            )
            continue

        # Get collection
        collection = (
            ee.ImageCollection(collection_id)
            .filterDate(new_init_date, new_final_date)
            .filterBounds(roi)
        )
        collection_lenght = collection.size().getInfo()
        logger.info(f"Total images: {collection_lenght}")

        if collection_lenght == 0:
            logger.warning("Coleção com 0 imagens, passando para a próxima coleção")
            continue

        min_date = collection.aggregate_min("system:time_start")
        max_date = collection.aggregate_max("system:time_start")

        min_date = ee.Date(min_date).format("YYYY-MM-dd").getInfo()
        max_date = ee.Date(max_date).format("YYYY-MM-dd").getInfo()

        logger.info(f"Donwload: {collection_id} collection")
        logger.info(f"Collection Date Availability: {min_date} - {max_date}")

        if not selected_bands:
            logger.warning("Download All Bands")
        else:
            new_selected_bands = get_original_bands_name(
                satelite=satelite_name,
                fake_name_bands=selected_bands,
                is_toa=is_TOA(collection_id),
            )
            logger.warning(f"Download Bands: {new_selected_bands}")

        images = collection.toList(collection.size()).getInfo()

        for i, image_info in enumerate(
            tqdm(images, desc="Downloading Images", unit="imagem")
        ):
            image_id = image_info["id"]
            image = ee.Image(image_id)

            # Filter if necessary
            if new_selected_bands:
                image = image.select(new_selected_bands)

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
            date = datetime.utcfromtimestamp(timestamp / 1000).strftime(
                "%Y-%m-%d"
            )  # Converte para data legível

            # Nome do arquivo de saída
            output_file = os.path.join(
                f"{dowload_path}{location_name}/{date[:4]}",
                f"{prefix_images_name}_{satelite_name}_{location_name}_{date}.tif",
            )

            # Faz o download da imagem e salva no diretório especificado
            response = requests.get(url)
            with open(output_file, "wb") as file:
                file.write(response.content)

    return True
