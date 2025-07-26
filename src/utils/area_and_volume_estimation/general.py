import json

import geopandas as gpd
from rasterio.io import MemoryFile
from rasterio.mask import mask


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


def media_mensal_por_ano(df, column="volume_m2"):
    """
    Calcula a média de valores para cada mês de cada ano.

    Parâmetros:
        df (pd.DataFrame): DataFrame com colunas ['ano', 'mes', 'valor'].

    Retorna:
        pd.DataFrame: Agrupado com média por ano e mês.
    """
    return (
        df.groupby(["year", "month"], as_index=False)
        .agg({f"{column}": "mean"})
        .sort_values(["year", "month"])
        .rename(columns={column: "volume_m2"})
    )


def medias_mensais_por_ano(df):
    """
    Calcula a média de cada coluna numérica para cada mês de cada ano.

    Parâmetros:
        df (pd.DataFrame): DataFrame com colunas ['year', 'month', ...outras colunas de volume...]

    Retorna:
        pd.DataFrame: média mensal por ano para todas as colunas (exceto 'year' e 'month').
    """
    colunas_para_media = df.select_dtypes(include='number').columns.difference(['year', 'month'])

    df_media = (
        df.groupby(['year', 'month'], as_index=False)[colunas_para_media]
        .mean()
        .sort_values(['year', 'month'])
    )

    return df_media

