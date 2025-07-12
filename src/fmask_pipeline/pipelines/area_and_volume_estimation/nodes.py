from turtle import pd
from pandas import DataFrame
from utils.area_and_volume_estimation.water import (
    calculate_water_area,
    calculate_volumes_to_multiple_methods,
)


def estimate_water_area(
    tif_path: str, path_shapefile: str, binarization_gt: int = 0, save_path: str = None
) -> tuple:
    """
    Reproject a .tif image with geographic CRS (degrees) to UTM (meters),
    and calculates the area of water pixels (value > 0).

    parameters:
    - tif_path (str): path to the .tif file
    - path_shapefile (str): path to the GeoJSON clipping file
    - binarization_gt (int): threshold value to consider a pixel as water
    - save_path (str): path to save the reprojected raster

    returns:
    - Tuple: (area_m2)
    """
    area_m2, area_km2 = calculate_water_area(
        tif_path, path_shapefile, binarization_gt, save_path
    )

    return area_m2


def estimate_water_volume(
    df_areas: DataFrame,
    df_cav_path: str,
    save_path: str,
    location,
    cav_area_column: str = "area",
    cav_volume_column: str = "volume",
    year_column: str = "year",
    month_column: str = "month",
    cloud_percentage_column: str = "CLOUDY_PIXEL_PERCENTAGE",
    areas_columns=[],
    escale: float = 1,
) -> tuple:
    """
    Reproject a .tif image with geographic CRS (degrees) to UTM (meters),
    and calculates the volume of water pixels (value > 0).

    parameters:
    - tif_path (str): path to the .tif file
    - path_shapefile (str): path to the GeoJSON clipping file
    - binarization_gt (int): threshold value to consider a pixel as water
    - save_path (str): path to save the reprojected raster

    returns:
    - Tuple: (volume_m3, volume_km3)
    """

    df_cav = pd.read_csv(df_cav_path)
    df_volume = calculate_volumes_to_multiple_methods(
        df_areas=df_areas,
        df_cav=df_cav,
        cav_area_column=cav_area_column,
        cav_volume_column=cav_volume_column,
        year_column=year_column,
        month_column=month_column,
        cloud_percentage_column=cloud_percentage_column,
        areas_columns=areas_columns,
        escale=escale,
    )

    df_volume.to_csv(f"{save_path}{location}/volumes.csv", index=False)

    return None
