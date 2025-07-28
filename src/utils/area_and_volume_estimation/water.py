import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import Resampling, calculate_default_transform, reproject
from scipy.signal import savgol_filter
from scipy.stats import zscore

from .general import crop_raster_with_geojson_obj


def calculate_water_area(tif_path, path_shapefile, binarization_gt=0, save_path=None):
    """
    Reprojeta uma imagem .tif com CRS geográfico (graus) para UTM (metros),
    e calcula a área de pixels de água (valor > 0).

    Parâmetros:
    - tif_path (str): caminho para o arquivo .tif

    Retorna:
    - Tuple: (area_m2, area_km2)
    """
    with rasterio.open(tif_path) as src:
        dst_crs = "EPSG:31984"  # SIRGAS 2000 / UTM zone 24S (Paraíba)
        src = crop_raster_with_geojson_obj(
            src, geojson_path=path_shapefile
        )  # Assuming you have a function to crop the raster

        profile = src.profile
        profile.update(count=1)
        if save_path:
            with rasterio.open(
                f"./data/areas_tif/{tif_path.split('/')[-1]}", "w", **profile
            ) as dst:
                dst.write(src.read()[0], 1)

        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )

        kwargs = src.meta.copy()
        kwargs.update(
            {"crs": dst_crs, "transform": transform, "width": width, "height": height}
        )

        with rasterio.MemoryFile() as memfile:
            with memfile.open(**kwargs) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=dst_crs,
                        resampling=Resampling.nearest,
                    )

                image = dst.read(1)
                pixel_width = abs(dst.transform.a)
                pixel_height = abs(dst.transform.e)
                pixel_area = pixel_width * pixel_height
                # pixel_area = 100

                water_pixels = np.sum(image > binarization_gt)
                water_area_m2 = water_pixels * pixel_area
                water_area_km2 = water_area_m2 / 1e6

                return water_area_m2, water_area_km2





def calculate_volumes_to_multiple_methods(
    df_areas: pd.DataFrame,
    df_cav: pd.DataFrame,
    cav_area_column="area",
    cav_volume_column="volume",
    year_column="year",
    month_column="month",
    cloud_percentage_column="CLOUDY_PIXEL_PERCENTAGE",
    areas_columns=[],
    escale: float = 1.0,
    window_size: int = 6,  # usado para média, mediana e savgol
    savgol_poly: int = 2   # grau do polinômio para Savitzky-Golay
):
    """Calcula volumes e aplica filtros (média, mediana, Savgol, Z-score)."""

    df_cav = df_cav.sort_values(cav_area_column).drop_duplicates(subset=[cav_area_column])
    min_area = df_cav[cav_area_column].min()
    max_area = df_cav[cav_area_column].max()

    df_volumes = pd.DataFrame()
    df_volumes["year"] = df_areas[year_column]
    df_volumes["month"] = df_areas[month_column]
    df_volumes["CLOUDY_PIXEL_PERCENTAGE"] = df_areas[cloud_percentage_column]

    for column in areas_columns:
        areas = df_areas[column].clip(lower=min_area, upper=max_area)
        volumes = np.interp(areas, df_cav[cav_area_column], df_cav[cav_volume_column]) / escale
        volume_col = f"volume_{column.replace('_area', '')}"
        df_volumes[volume_col] = volumes

        # Média móvel
        df_volumes[f"{volume_col}_mean"] = df_volumes[volume_col].rolling(window=window_size, min_periods=1, center=True).mean()

        # Mediana móvel
        df_volumes[f"{volume_col}_median"] = df_volumes[volume_col].rolling(window=window_size, min_periods=1, center=True).median()

        # Savitzky-Golay
        if len(df_volumes) >= window_size:
            df_volumes[f"{volume_col}_savgol"] = savgol_filter(df_volumes[volume_col], window_length=window_size, polyorder=savgol_poly, mode='interp')
        else:
            df_volumes[f"{volume_col}_savgol"] = df_volumes[volume_col]  # fallback

        # Z-score (com outliers substituídos por NaN)
        z_scores = zscore(df_volumes[volume_col], nan_policy="omit")
        mask = np.abs(z_scores) > 3
        filtered = df_volumes[volume_col].copy()
        filtered[mask] = np.nan
        df_volumes[f"{volume_col}_zscore"] = filtered

    return df_volumes

