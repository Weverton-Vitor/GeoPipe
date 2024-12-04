import datetime
import ee
import geopandas as gpd
import geojson
import requests
import os
from tqdm import tqdm


def donwload_images(
    collection_id: str,
    dowload_path: str,
    init_date: str,
    final_date: str,
    roi_path: str,
    prefix_images_name: str,
    all_bands=True,
) -> None:
    os.makedirs(dowload_path, exist_ok=True)

    roi = shapefile2feature_collection(roi_path)

    collection = (
        ee.ImageCollection(collection_id)
        .filterDate(init_date, final_date)
        .filterBounds(roi)
    )

    print(collection.first().geometry().projection().getInfo())

    # Filter if necessary
    if not all_bands:
        collection = collection.select(["B2", "B3", "B4", "B8", "B11", "B12"])

    print("Total Imagens:", collection.size().getInfo())

    images = collection.toList(collection.size()).getInfo()

    for i, image_info in enumerate(
        tqdm(images, desc="Downloading Images", unit="imagem")
    ):
        image_id = image_info["id"]
        image = ee.Image(image_id)

        url = image.getDownloadURL(
            {
                "scale": 10,  # Resolução espacial
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
        output_file = os.path.join(dowload_path, f"{prefix_images_name}_{date}.tif")

        # Faz o download da imagem e salva no diretório especificado
        response = requests.get(url)
        with open(output_file, "wb") as file:
            file.write(response.content)

        

    print(f"Imagem {i + 1} baixada: {output_file}")


def shapefile2feature_collection(shapefile_path: str) -> ee.FeatureCollection:
    # Loading the shapefile .zip format
    gdf = gpd.read_file(shapefile_path)

    # Convert from GeoDataFrame to GeoJson
    geojson_data = geojson.loads(gdf.to_json())

    # Create the FeatureCollection from geojson
    fc = ee.FeatureCollection(geojson_data)

    return fc
