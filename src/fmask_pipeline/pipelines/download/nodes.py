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

from utils.download.download import is_TOA

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


def get_original_bands_name(satelite: str, fake_name_bands: list, is_toa: bool):
    band_prefix = "" if is_toa else "SR_"
    band_prefix_thermal = "" if is_toa else "ST_"

    band_mappings = {
        "LT05": {
            "coastal": None,
            "blue": f"{band_prefix}B1",
            "green": f"{band_prefix}B2",
            "red": f"{band_prefix}B3",
            "nir": f"{band_prefix}B4",
            "swir1": f"{band_prefix}B5",
            "swir2": f"{band_prefix}B7",
            "pan": None,
            "cirrus": None,
            "thermal1": f"{band_prefix_thermal}B6",
            "thermal2": None,
            "QA_PIXEL": "BQA",
        },
        "LE07": {
            "coastal": None,
            "blue": f"{band_prefix}B1",
            "green": f"{band_prefix}B2",
            "red": f"{band_prefix}B3",
            "nir": f"{band_prefix}B4",
            "swir1": f"{band_prefix}B5",
            "swir2": f"{band_prefix}B7",
            "pan": f"{band_prefix}B8",
            "cirrus": None,
            "thermal1": f"{band_prefix_thermal}B6",
            "thermal2": None,
            "QA_PIXEL": "QA_PIXEL",
        },
        "LC08": {
            "coastal": f"{band_prefix}B1",
            "blue": f"{band_prefix}B2",
            "green": f"{band_prefix}B3",
            "red": f"{band_prefix}B4",
            "nir": f"{band_prefix}B5",
            "swir1": f"{band_prefix}B6",
            "swir2": f"{band_prefix}B7",
            "pan": f"{band_prefix}B8",
            "cirrus": f"{band_prefix}B9",
            "thermal1": f"{band_prefix_thermal}B10",
            "thermal2": f"{band_prefix}B11",
            "QA_PIXEL": "QA_PIXEL",
        },
        "LC09": {
            "coastal": "B1",
            "blue": f"{band_prefix}B2",
            "green": f"{band_prefix}B3",
            "red": f"{band_prefix}B4",
            "nir": f"{band_prefix}B5",
            "swir1": f"{band_prefix}B6",
            "swir2": f"{band_prefix}B7",
            "pan": f"{band_prefix}B8",
            "cirrus": f"{band_prefix}B9",
            "thermal1": f"{band_prefix_thermal}B10",
            "thermal2": f"{band_prefix}B11",
            "QA_PIXEL": "QA_PIXEL",
        },
        "S2_SR_HARMONIZED": {
            "coastal": "B1",
            "blue": "B2",
            "green": "B3",
            "red": "B4",
            "rededge1": "B5",
            "rededge2": "B6",
            "rededge3": "B7",
            "nir": "B8",
            "nir_narrow": "B8A",
            "swir1": "B11",
            "swir2": "B12",
            "cirrus": "B10",
            "QA_PIXEL": "QA60",
        },
    }

    # Adding toa collection to Sentinel
    band_mappings["S2_HARMONIZED"] = band_mappings["S2_SR_HARMONIZED"]

    return (
        [band_mappings[satelite].get(band, None) for band in fake_name_bands]
        if satelite in band_mappings
        else []
    )


def adjust_date(satelite: str, start_date_str: str, end_date_str: str) -> tuple:
    satellite_dates = {
        "LT05": ("1984-03-01", "2013-06-05"),
        "LE07": ("1999-04-15", None),  # Ainda operacional
        "LC08": ("2013-02-11", None),  # Ainda operacional
        "LC09": ("2021-09-27", None),  # Ainda operacional
        "S2": ("2015-06-23", None),  # Sentinel-2A lançado em 2015
    }

    if satelite not in satellite_dates:
        raise ValueError(f"Satélite {satelite} não reconhecido.")

    sat_start_date, sat_end_date = satellite_dates[satelite]
    sat_start_date = datetime.strptime(sat_start_date, "%Y-%m-%d")
    sat_end_date = datetime.strptime(sat_end_date, "%Y-%m-%d") if sat_end_date else None

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    if start_date < sat_start_date:
        start_date = sat_start_date
    if sat_end_date and start_date > sat_end_date:
        start_date = sat_end_date

    if end_date < sat_start_date:
        end_date = sat_start_date
    if sat_end_date and end_date > sat_end_date:
        end_date = sat_end_date

    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def validate_date(satelite: str, date_str: str):
    satellite_dates = {
        "LT05": ("1984-03-01", "2013-06-05"),
        "LE07": ("1999-04-15", None),  # Ainda operacional
        "LC08": ("2013-02-11", None),  # Ainda operacional
        "LC09": ("2021-09-27", None),  # Ainda operacional
        "S2": ("2015-06-23", None),  # Sentinel-2A lançado em 2015
    }

    if satelite not in satellite_dates:
        raise ValueError(f"Satélite {satelite} não reconhecido.")

    start_date, end_date = satellite_dates[satelite]
    input_date = datetime.strptime(date_str, "%Y-%m-%d")
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

    if input_date < start_date:
        raise ValueError(
            f"Erro: A data {date_str} é anterior ao início do satélite {satelite} ({start_date.date()})."
        )
    if end_date and input_date > end_date:
        raise ValueError(
            f"Erro: A data {date_str} é posterior ao fim do satélite {satelite} ({end_date.date()})."
        )

    return True


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
            selected_bands = get_original_bands_name(
                satelite=satelite_name,
                fake_name_bands=selected_bands,
                is_toa=is_TOA(collection_id),
            )
            logger.warning(f"Download Bands: {selected_bands}")

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
