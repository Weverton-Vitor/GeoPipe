import datetime
import logging
import os

import ee
import geojson
import geopandas as gpd
import requests
from tqdm import tqdm



# Obter o logger específico do node
logger = logging.getLogger(__name__)

def donwload_images(
    collection_id: str,
    dowload_path: str,
    init_date: str,
    final_date: str,
    roi: ee.FeatureCollection,
    prefix_images_name: str,
    all_bands: bool=True,
    scale :int=10
) -> None:
    
    # Create directories structure
    os.makedirs(dowload_path, exist_ok=True)
    
    for year in range(int(init_date.split('-')[0]), int(final_date.split('-')[0])+1):
        os.makedirs(f'{dowload_path}{year}', exist_ok=True)


    # Get collection
    collection = (
        ee.ImageCollection(collection_id)
        .filterDate(init_date, final_date)
        .filterBounds(roi)
    )

    # Filter if necessary
    if not all_bands:
        logger.warning("Download bands: [B2, B3, B4, B8, B11, B12]")

    logger.info(f"Total images: {collection.size().getInfo()}")

    images = collection.toList(collection.size()).getInfo()

    for i, image_info in enumerate(
        tqdm(images, desc="Downloading Images", unit="imagem")
    ):
        image_id = image_info["id"]
        image = ee.Image(image_id)
        
        # Filter if necessary
        if not all_bands:
            image = image.select(["B2", "B3", "B4", "B8", "B11", "B12"])

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
        output_file = os.path.join(f'{dowload_path}/{date[:4]}', f"{prefix_images_name}_{date}.tif")

        # Faz o download da imagem e salva no diretório especificado
        response = requests.get(url)
        with open(output_file, "wb") as file:
            file.write(response.content)



def shapefile2feature_collection(shapefile: gpd.GeoDataFrame) -> ee.FeatureCollection:
    # Convert from GeoDataFrame to GeoJson
    geojson_data = geojson.loads(shapefile.to_json())

    # Create the FeatureCollection from geojson
    fc = ee.FeatureCollection(geojson_data)

    return fc
