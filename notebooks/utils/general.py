import json
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.io import MemoryFile


def crop_raster_with_geojson_obj(src, geojson_path):
    """
    Recorta um raster aberto (`src`) com base em um GeoJSON e retorna um novo objeto raster já recortado.

    Parâmetros:
        src (rasterio.io.DatasetReader): Objeto raster já aberto.
        geojson_path (str): Caminho para o GeoJSON com as geometrias.

    Retorna:
        rasterio.io.DatasetReader: Novo raster recortado (em memória).
    """
    # Lê o GeoJSON
    gdf = gpd.read_file(geojson_path)

    # Garante que está no mesmo CRS
    if gdf.crs != src.crs:
        gdf = gdf.to_crs(src.crs)

    # Extrai todas as geometrias
    geometrias = [
        feature["geometry"] for feature in json.loads(gdf.to_json())["features"]
    ]

    # Faz o recorte
    imagem_cortada, transform = mask(src, geometrias, crop=True)

    # Atualiza perfil
    perfil = src.profile.copy()
    perfil.update(
        {
            "height": imagem_cortada.shape[1],
            "width": imagem_cortada.shape[2],
            "transform": transform,
        }
    )

    # Cria um raster em memória e retorna como src
    memfile = MemoryFile()
    with memfile.open(**perfil) as dataset:
        dataset.write(imagem_cortada)

    return memfile.open()  # reabre para leitura
