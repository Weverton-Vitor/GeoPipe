import glob
import logging
import os

import pandas as pd
from pandas import DataFrame
from scipy.ndimage import median_filter
from scipy.signal import savgol_filter
from scipy.stats import zscore
from tqdm import tqdm

from utils.area_and_volume_estimation.general import media_mensal_por_ano
from utils.area_and_volume_estimation.plots import (
    plot_series_ano_mes,
    plot_water_over_time,
    plot_water_x_cloud_percent_over_time,
    plot_year_x_variable,
)
from utils.area_and_volume_estimation.water import (
    calculate_volumes_to_multiple_methods,
    calculate_water_area,
)

logger = logging.getLogger(__name__)


def estimate_water_area(
    water_masks_path: str,
    path_shapefile: str,
    save_path: str,
    location_name: str,
    binarization_gt: int = 0,
    *args,
    **kwargs,
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

    df_metadata = pd.read_csv(
        f"data/02_boa_images/{location_name}/metadata/{location_name}_metadata.csv"
    )
    df_areas = pd.DataFrame()
    masks = []
    days = []
    months = []
    years = []
    m2_areas = []
    km2_areas = []

    water_masks_path = water_masks_path + f"{location_name}/"
    water_masks = glob.glob(
        os.path.join(water_masks_path, "**", "*.tif"), recursive=True
    )
    logger.info(f"Found {len(water_masks)} tif files in {water_masks_path}")
    total_tifs = len(water_masks)

    with tqdm(total=total_tifs, desc="Estimate Volume", unit="images") as pbar:
        for mask_path in water_masks:
            area_m2, area_km2 = calculate_water_area(
                tif_path=mask_path,
                path_shapefile=path_shapefile,
                binarization_gt=binarization_gt,
            )

            year = mask_path.replace("_clean", "").split("/")[-1].split("_")[-1][:4]
            month = mask_path.replace("_clean", "").split("/")[-1].split("_")[-1][4:6]
            day = mask_path.replace("_clean", "").split("/")[-1].split("_")[-1][6:8]

            years.append(year)
            months.append(month)
            days.append(day)

            masks.append(mask_path)
            m2_areas.append(area_m2)
            km2_areas.append(area_km2)
            pbar.update(1)

    df_areas["water_masks"] = pd.Series(water_masks)
    df_areas["year"] = pd.Series(years)
    df_areas["month"] = pd.Series(months)
    df_areas["day"] = pd.Series(days)
    df_areas["m2_area"] = pd.Series(m2_areas)
    df_areas["km2_area"] = pd.Series(km2_areas)
    df_areas["CLOUDY_PIXEL_PERCENTAGE"] = 0  # df_metadata["CLOUDY_PIXEL_PERCENTAGE"]

    os.makedirs(f"{save_path}{location_name}", exist_ok=True)
    df_areas.to_csv(f"{save_path}{location_name}/df_areas.csv", index=False)

    return df_areas


def estimate_water_volume(
    water_areas_df: DataFrame,
    cav_path: str,
    save_path: str,
    location_name,
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

    df_cav = pd.read_csv(cav_path)
    df_volume = calculate_volumes_to_multiple_methods(
        df_areas=water_areas_df,
        df_cav=df_cav,
        cav_area_column=cav_area_column,
        cav_volume_column=cav_volume_column,
        year_column=year_column,
        month_column=month_column,
        cloud_percentage_column=cloud_percentage_column,
        areas_columns=areas_columns,
        escale=escale,
    )

    df_volume.to_csv(f"{save_path}{location_name}/volumes.csv", index=False)

    return df_volume


def plot_results(
    areas_df: DataFrame,
    volumes_df: DataFrame,
    location_name: str,
    save_path: str,
    method_name: str,
    ground_truth_name: str,
    ground_truth_path_df: str,
    ground_truth_column_volume: str = "Volume Útil (hm³)",
    ground_truth_column_date: str = "Data da Medição",
    escale: int = 1e6,
) -> bool:
    """
    Plot the results of water area and volume estimation.

    parameters:
    - df_areas (DataFrame): DataFrame containing water areas
    - df_volumes (DataFrame): DataFrame containing water volumes
    - location (str): location name for saving plots
    - save_path (str): path to save the plots
    """

    volumes_df = volumes_df.loc[volumes_df["CLOUDY_PIXEL_PERCENTAGE"] < 100]
    final_dir = f"{save_path}{location_name}/plots"
    os.makedirs(f"{final_dir}", exist_ok=True)

    logger.info(f"Saving plots to {final_dir}")

    logger.info("Plotting areas...")
    areas_mean_df = media_mensal_por_ano(areas_df, column="m2_area")

    logger.info("Plotting volumes...")

    gound_truth_df = pd.read_csv(ground_truth_path_df)
    gound_truth_df["year"] = gound_truth_df[ground_truth_column_date].apply(
        lambda x: x.split("/")[-1]
    )
    gound_truth_df["month"] = gound_truth_df[ground_truth_column_date].apply(
        lambda x: x.split("/")[-2]
    )
    gound_truth_df[ground_truth_column_volume] = gound_truth_df[
        ground_truth_column_volume
    ].apply(lambda x: float(x.replace(",", ".")) if isinstance(x, str) else x)

    gound_truth_df["volume_m2"] = gound_truth_df[ground_truth_column_volume].apply(
        lambda x: x * 1000000 / escale
    )

    ground_truth_mean_df = media_mensal_por_ano(
        gound_truth_df,
        column="volume_m2",
    )

    volumes_mean_df = media_mensal_por_ano(
        volumes_df,
        column=[column for column in list(volumes_df.columns) if "volume" in column][0],
    )

    volumes_df = volumes_df.rename(
        columns={
            [column for column in list(volumes_df.columns) if "volume" in column][
                0
            ]: "volume_m2"
        }
    )

    figure1 = plot_series_ano_mes(
        {
            f"{method_name}": volumes_df,
            ground_truth_name: gound_truth_df,
        },
        data_inicio="01/2019",
        data_fim="06/2025",
        titulo=f"{method_name} X {ground_truth_name} ao longo do tempo",
    )

    volumes_mean_mean_filter_df = volumes_df.copy()
    volumes_mean_mean_filter_df["volume_m2"] = (
        volumes_mean_mean_filter_df["volume_m2"].rolling(window=5, center=True).mean()
    )

    figure2 = plot_series_ano_mes(
        {
            f"{method_name}": volumes_mean_mean_filter_df,
            ground_truth_name: gound_truth_df,
        },
        data_inicio="01/2019",
        data_fim="06/2025",
        titulo=f"{method_name} X {ground_truth_name} ao longo do tempo (filtro da média)",
    )

    volumes_mean_savgol_filter_df = volumes_df.copy()
    try:
        volumes_mean_savgol_filter_df["volume_m2"] = savgol_filter(
            volumes_mean_savgol_filter_df["volume_m2"], window_length=10, polyorder=4
        )
    except ValueError as e:
        logger.error(f"Error applying Savgol filter: {e}")
        for i in range(10, 0, -1):
            try:
                volumes_mean_savgol_filter_df["volume_m2"] = savgol_filter(
                    volumes_mean_savgol_filter_df["volume_m2"],
                    window_length=i,
                    polyorder=4,
                )
                logger.info(f"Applied Savgol filter with window length {i}")
                break
            except ValueError as e:
                logger.error(
                    f"Error applying Savgol filter with window length {i}: {e}"
                )

    figure3 = plot_series_ano_mes(
        {
            f"{method_name}": volumes_mean_savgol_filter_df,
            ground_truth_name: gound_truth_df,
        },
        data_inicio="01/2019",
        data_fim="06/2025",
        titulo=f"{method_name} X {ground_truth_name} ao longo do tempo (filtro de savgol)",
    )

    volumes_mean_median_filter_df = volumes_df.copy()
    volumes_mean_savgol_filter_df["volume_m2"] = median_filter(
        volumes_mean_median_filter_df["volume_m2"], size=20
    )

    figure4 = plot_series_ano_mes(
        {
            f"{method_name}": volumes_mean_savgol_filter_df,
            ground_truth_name: gound_truth_df,
        },
        data_inicio="01/2019",
        data_fim="06/2025",
        titulo=f"{method_name} X {ground_truth_name} ao longo do tempo (filtro da mediana)",
    )

    volumes_mean_z_index_savgol_filter_df = volumes_df.copy()
    volumes_mean_z_index_savgol_filter_df["z"] = zscore(
        volumes_mean_z_index_savgol_filter_df["volume_m2"]
    )
    volumes_mean_z_index_savgol_filter_df = volumes_mean_z_index_savgol_filter_df[
        volumes_mean_z_index_savgol_filter_df["z"].abs() < 2
    ]  # remove outliers com z > 2

    try:
        volumes_mean_z_index_savgol_filter_df["volume_m2"] = savgol_filter(
            volumes_mean_z_index_savgol_filter_df["volume_m2"],
            window_length=25,
            polyorder=4,
        )
    except ValueError as e:
        logger.error(f"Error applying Savgol filter: {e}")
        for i in range(25, 0, -1):
            try:
                poly = 4
                if i == 4:
                    poly = 2
                volumes_mean_z_index_savgol_filter_df["volume_m2"] = savgol_filter(
                    volumes_mean_z_index_savgol_filter_df["volume_m2"],
                    window_length=i,
                    polyorder=2,
                )
                logger.info(f"Applied Savgol filter with window length {i}")
                break
            except ValueError as e:
                logger.error(
                    f"Error applying Savgol filter with window length {i}: {e}"
                )

    figure5 = plot_series_ano_mes(
        {
            f"{method_name}": volumes_mean_savgol_filter_df,
            ground_truth_name: gound_truth_df,
        },
        data_inicio="01/2019",
        data_fim="06/2025",
        titulo=f"{method_name} X {ground_truth_name} ao longo do tempo (filtro da savgol + zscore)",
    )

    # Mean

    figure1_mean = plot_series_ano_mes(
        {
            f"{method_name}": volumes_mean_df,
            ground_truth_name: ground_truth_mean_df,
        },
        data_inicio="01/2019",
        data_fim="06/2025",
        titulo=f"{method_name} X {ground_truth_name} ao longo do tempo (média mensal)",
    )

    volumes_mean_mean_filter_df = volumes_mean_df.copy()
    volumes_mean_mean_filter_df["volume_m2"] = (
        volumes_mean_mean_filter_df["volume_m2"].rolling(window=5, center=True).mean()
    )

    figure2_mean = plot_series_ano_mes(
        {
            f"{method_name}": volumes_mean_mean_filter_df,
            ground_truth_name: ground_truth_mean_df,
        },
        data_inicio="01/2019",
        data_fim="06/2025",
        titulo=f"{method_name} X {ground_truth_name} ao longo do tempo (média mensal + filtro da média)",
    )

    volumes_mean_savgol_filter_df = volumes_mean_df.copy()
    print(volumes_mean_savgol_filter_df["volume_m2"].shape)
    try:
        volumes_mean_savgol_filter_df["volume_m2"] = savgol_filter(
            volumes_mean_savgol_filter_df["volume_m2"],
            window_length=25,
            polyorder=4,
        )
    except ValueError as e:
        logger.error(f"Error applying Savgol filter: {e}")
        for i in range(25, 0, -1):
            try:
                poly = 4
                if i == 4:
                    poly = 2
                volumes_mean_savgol_filter_df["volume_m2"] = savgol_filter(
                    volumes_mean_savgol_filter_df["volume_m2"],
                    window_length=i,
                    polyorder=2,
                )
                logger.info(f"Applied Savgol filter with window length {i}")
                break
            except ValueError as e:
                logger.error(
                    f"Error applying Savgol filter with window length {i}: {e}"
                )

    figure3_mean = plot_series_ano_mes(
        {
            f"{method_name}": volumes_mean_savgol_filter_df,
            ground_truth_name: ground_truth_mean_df,
        },
        data_inicio="01/2019",
        data_fim="06/2025",
        titulo=f"{method_name} X {ground_truth_name} ao longo do tempo (média mensal + filtro de savgol)",
    )

    volumes_mean_median_filter_df = volumes_mean_df.copy()
    volumes_mean_median_filter_df["volume_m2"] = median_filter(
        volumes_mean_median_filter_df["volume_m2"], size=20
    )

    figure4_mean = plot_series_ano_mes(
        {
            f"{method_name}": volumes_mean_median_filter_df,
            ground_truth_name: ground_truth_mean_df,
        },
        data_inicio="01/2019",
        data_fim="06/2025",
        titulo=f"{method_name} X {ground_truth_name} ao longo do tempo (média mensal + filtro da mediana)",
    )

    volumes_mean_z_index_savgol_filter_df = volumes_mean_df.copy()
    volumes_mean_z_index_savgol_filter_df["z"] = zscore(
        volumes_mean_z_index_savgol_filter_df["volume_m2"]
    )
    volumes_mean_z_index_savgol_filter_df = volumes_mean_z_index_savgol_filter_df[
        volumes_mean_z_index_savgol_filter_df["z"].abs() < 2
    ]  # remove outliers com z > 2

    try:
        volumes_mean_z_index_savgol_filter_df["volume_m2"] = savgol_filter(
            volumes_mean_z_index_savgol_filter_df["volume_m2"],
            window_length=25,
            polyorder=4,
        )
    except ValueError as e:
        logger.error(f"Error applying Savgol filter: {e}")
        for i in range(25, 0, -1):
            try:
                volumes_mean_z_index_savgol_filter_df["volume_m2"] = savgol_filter(
                    volumes_mean_z_index_savgol_filter_df["volume_m2"],
                    window_length=i,
                    polyorder=4,
                )
                logger.info(f"Applied Savgol filter with window length {i}")
                break
            except ValueError as e:
                logger.error(
                    f"Error applying Savgol filter with window length {i}: {e}"
                )

    figure5_mean = plot_series_ano_mes(
        {
            f"{method_name}": volumes_mean_z_index_savgol_filter_df,
            ground_truth_name: ground_truth_mean_df,
        },
        data_inicio="01/2019",
        data_fim="06/2025",
        titulo=f"{method_name} X {ground_truth_name} ao longo do tempo (média mensal + filtro da savgol + zscore)",
    )

    # Saving figures

    figure1.savefig(
        f"{final_dir}/{method_name}_vs_{ground_truth_name}_ao_longo_do_tempo.png",
        bbox_inches="tight",
    )

    figure2.savefig(
        f"{final_dir}/{method_name}_vs_{ground_truth_name}_ao_longo_do_tempo_filtro_da_media.png",
        bbox_inches="tight",
    )

    figure3.savefig(
        f"{final_dir}/{method_name}_vs_{ground_truth_name}_ao_longo_do_tempo_filtro_da_savgol.png",
        bbox_inches="tight",
    )

    figure4.savefig(
        f"{final_dir}/{method_name}_vs_{ground_truth_name}_ao_longo_do_tempo_filtro_da_mediana.png",
        bbox_inches="tight",
    )

    figure5.savefig(
        f"{final_dir}/{method_name}_vs_{ground_truth_name}_ao_longo_do_tempo_zscore_filtro_de_savgol.png",
        bbox_inches="tight",
    )

    figure1_mean.savefig(
        f"{final_dir}/{method_name}_vs_{ground_truth_name}_ao_longo_do_tempo_media.png",
        bbox_inches="tight",
    )

    figure2_mean.savefig(
        f"{final_dir}/{method_name}_vs_{ground_truth_name}_ao_longo_do_tempo_media_filtro_da_media.png",
        bbox_inches="tight",
    )

    figure3_mean.savefig(
        f"{final_dir}/{method_name}_vs_{ground_truth_name}_ao_longo_do_tempo_media_filtro_da_savgol.png",
        bbox_inches="tight",
    )

    figure4_mean.savefig(
        f"{final_dir}/{method_name}_vs_{ground_truth_name}_ao_longo_do_tempo_media_filtro_da_mediana.png",
        bbox_inches="tight",
    )

    figure5_mean.savefig(
        f"{final_dir}/{method_name}_vs_{ground_truth_name}_ao_longo_do_tempo_media_zscore_filtro_da_savgol.png",
        bbox_inches="tight",
    )

    return True
