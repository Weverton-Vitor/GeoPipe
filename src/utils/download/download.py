import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import ee
import pandas as pd
import requests
from tqdm import tqdm

from utils.gee.authenticate import authenticate_earth_engine

logger = logging.getLogger(__name__)


def is_TOA(colecao):
    """
    Verifica se a coleção do Google Earth Engine (GEE) é BOA (Bottom of Atmosphere)
    ou TOA (Top of Atmosphere), com base no nome da coleção.

    Parâmetros:
        colecao (str): Nome da coleção no GEE.

    Retorno:
        str: 'BOA' se a coleção for de Reflectância de Superfície,
             'TOA' se a coleção for de Reflectância de Topo da Atmosfera,
             'Desconhecido' se não for possível determinar.
    """
    # Padrões comuns de coleções TOA e BOA
    if "TOA" in colecao.upper() and "SR" not in colecao.upper():
        return True

    return False


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
            "QA_PIXEL": "QA_PIXEL",
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
        "S2": {
            "coastal": "B1",
            "blue": "B2",
            "green": "B3",
            "red": "B4",
            "rededge1": "B5",
            "rededge2": "B6",
            "rededge3": "B7",
            "nir": "B8",
            "nir_narrow": "B8A",
            "water_vapour": "B9",
            "cirrus": "B10",
            "swir1": "B11",
            "swir2": "B12",
            "QA_PIXEL": "QA60",
        },
        "S2_SR": {
            "coastal": "B1",
            "blue": "B2",
            "green": "B3",
            "red": "B4",
            "rededge1": "B5",
            "rededge2": "B6",
            "rededge3": "B7",
            "nir": "B8",
            "nir_narrow": "B8A",
            "water_vapour": "B9",
            "swir1": "B11",
            "swir2": "B12",
            "QA_PIXEL": "QA60",
        },
    }

    bands = (
        [band_mappings[satelite].get(band, None) for band in fake_name_bands]
        if satelite in band_mappings
        else []
    )
    if None in bands:
        bands.remove(None)  # Remove None values

    return bands


def adjust_date(satelite: str, start_date_str: str, end_date_str: str) -> tuple:
    satellite_dates = {
        "LT05": ("1984-03-01", "2013-06-05"),
        "LE07": ("1999-04-15", None),  # Ainda operacional
        "LC08": ("2013-02-11", None),  # Ainda operacional
        "LC09": ("2021-09-27", None),  # Ainda operacional
        "S2": ("2015-06-23", None),  # Sentinel-2A lançado em 2015
        "S2_SR": ("2015-06-23", None),  # Sentinel-2A lançado em 2015
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
        "S2_SR": ("2015-06-23", None),  # Sentinel-2A lançado em 2015
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


def download_image(
    image_id: Path,
    output_file: str,
    selected_bands: list,
    roi: ee.FeatureCollection = None,
    scale: int = 10,
):
    try:
        image = ee.Image(image_id)

        # Filter if necessary
        if selected_bands:
            image = image.select(selected_bands)

        url = None
        if roi is None:
            # Download the image without a region of interest
            url = image.getDownloadURL(
                {
                    "scale": scale,  # Resolução espacial
                    "crs": "EPSG:4326",  # Sistema de coordenadas
                    "format": "GeoTIFF",  # Formato de saída
                }
            )
        else:
            url = image.getDownloadURL(
                {
                    "scale": scale,  # Resolução espacial
                    "region": roi.geometry(),  # Região de interesse
                    "crs": "EPSG:4326",  # Sistema de coordenadas
                    "format": "GeoTIFF",  # Formato de saída
                }
            )

        # Get image information
        image_info = get_image_metadata(image)

        # Get date of image and convert to readable format
        #timestamp = image_info["properties"]["system:time_start"]  # Timestamp Unix
        #date = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).strftime(
        #    "%Y-%m-%d"
        #)

        # Nome do arquivo de saída
        # output_file = os.path.join(
        #     f"{dowload_path}{location_name}/{date[:4]}",
        #     f"{prefix_images_name}_{satelite_name}_{location_name}_{date}.tif",
        # )

        # Faz o download da imagem e salva no diretório especificado
        response = requests.get(url)
        with open(output_file, "wb") as file:
            file.write(response.content)

        return image_info

    except Exception as e:
        logger.error(f"Erro ao baixar a imagem {image_id}: {e}")


def save_metadata_as_csv(
    metadata: list[dict],
    output_path: str,
    prefix: str = "",
    suffix: str = "",
) -> bool:
    """
    Salva os metadados em um arquivo CSV.

    Parâmetros:
        metadata (dict): Dicionário contendo os metadados a serem salvos.
        output_path (str): Caminho do diretório onde o arquivo CSV será salvo.
        prefix (str, opcional): Prefixo para o nome do arquivo. Padrão é "".
        suffix (str, opcional): Sufixo para o nome do arquivo. Padrão é "".

    Retorno:
        bool: True se o arquivo foi salvo com sucesso, False caso contrário.
    """
    # Cria o diretório de saída, se não existir
    os.makedirs(output_path, exist_ok=True)

    # Cria o nome do arquivo CSV
    file_name = f"{prefix}_metadata_{suffix}.csv"
    file_path = os.path.join(output_path, file_name)

    # Converte o dicionário de metadados em um DataFrame do pandas
    df = pd.DataFrame(metadata)

    # Salva o DataFrame como um arquivo CSV
    df.to_csv(file_path, index=False)

    return True


def get_image_metadata(image):
    """
    Extracts metadata from an Earth Engine Image and returns it as a Python dictionary.

    Parameters:
        image (ee.Image): The Earth Engine image object.

    Returns:
        dict: A dictionary containing image metadata properties.
    """
    if not isinstance(image, ee.Image):
        raise TypeError("Input must be an ee.Image")

    # Get the image properties as a dictionary
    properties = image.toDictionary().getInfo()

    return properties


if __name__ == "__main__":
    key_path = Path("/media/weverton/D/Dev/python/Remote Sensing/tcc/GeoPipe/key.json")
    authenticate_earth_engine(key_path)

    download_image(
        image_id="COPERNICUS/S2_SR/20210101T133239_20210101T133237_T22WEB",
        dowload_path="/path/to/download/",
        location_name="location_name",
        prefix_images_name="prefix",
        satelite_name="LC09",
        selected_bands=["B4", "B5"],
        scale=10,
    )
