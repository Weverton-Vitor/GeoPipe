import glob
import logging
import os

import pandas as pd
from pandas import DataFrame
from tqdm import tqdm

from utils.area_and_volume_estimation.general import (
    media_mensal_por_ano,
    medias_mensais_por_ano,
)
from utils.area_and_volume_estimation.plots import (
    plot_series_ano_mes,
)
from utils.area_and_volume_estimation.water import (
    calculate_volumes_to_multiple_methods,
    calculate_water_area,
)
from utils.metrics.regression import calculate_metrics_regression_by_month

logger = logging.getLogger(__name__)


def estimate_water_area(
    water_masks_path: str,
    path_shapefile: str,
    save_path: str,
    location_name: str,
    thresholds: list,
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
    dfs = {}
    for threshold in thresholds:
        # df_metadata = pd.read_csv(
        #     f"data/02_boa_images/{location_name}/metadata/{location_name}_metadata.csv"
        # )
        df_areas = pd.DataFrame()
        masks = []
        days = []
        months = []
        years = []
        m2_areas = []
        km2_areas = []

        masks_path = water_masks_path + f"{location_name}/"
        water_masks = glob.glob(
            os.path.join(masks_path, "**", "*.tif"), recursive=True
        )
        logger.info(f"Found {len(water_masks)} tif files in {masks_path}")
        total_tifs = len(water_masks)

        logger.info(f"Threshold: {threshold}")

        with tqdm(total=total_tifs, desc="Estimate Volume", unit="images") as pbar:
            for mask_path in water_masks:
                area_m2, area_km2 = calculate_water_area(
                    tif_path=mask_path,
                    path_shapefile=path_shapefile,
                    threshold=threshold,
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
        df_areas["CLOUDY_PIXEL_PERCENTAGE"] = 0 # df_metadata["CLOUDY_PIXEL_PERCENTAGE"]

        os.makedirs(f"{save_path}{location_name}", exist_ok=True)
        df_areas.to_csv(f"{save_path}{location_name}/df_areas_trh_{threshold}.csv", index=False)
        dfs[f"df_areas_trh_{threshold}"] = df_areas

    return dfs


def estimate_water_volume(
    water_areas_dfs: dict,
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
    dfs = {}
    for key, df in water_areas_dfs.items():
        df_cav = pd.read_csv(cav_path)
        df_volume = calculate_volumes_to_multiple_methods(
            df_areas=df,
            df_cav=df_cav,
            cav_area_column=cav_area_column,
            cav_volume_column=cav_volume_column,
            year_column=year_column,
            month_column=month_column,
            cloud_percentage_column=cloud_percentage_column,
            areas_columns=areas_columns,
            escale=escale,
        )

        df_volume.to_csv(f"{save_path}{location_name}/{key.replace('areas', 'volumes')}.csv", index=False)
        dfs[key.replace('areas', 'volumes')] = df_volume
    return dfs


def calculate_metrics(
    path_real_df: str,
    pred_dfs: pd.DataFrame,
    save_path: str,
    col_real: str,
    location_name: str,
    # col_pred: str,
    *args,
    **kwargs,
) -> bool:
    logger.info("Calculating metrics")
    real_df = pd.read_csv(path_real_df)

    real_df["year"] = real_df["Data da Medição"].apply(lambda x: x.split("/")[-1])
    real_df["month"] = real_df["Data da Medição"].apply(lambda x: x.split("/")[-2])
    real_df["Volume Útil (hm³)"] = real_df["Volume Útil (hm³)"].apply(
        lambda x: float(x.replace(",", ".")) if isinstance(x, str) else x
    )

    real_df["volume_m2_real"] = real_df["Volume Útil (hm³)"].apply(
        lambda x: x * 1000000 / 1e6
    )

    real_df = media_mensal_por_ano(
        real_df,
        column="volume_m2_real",
    )

    real_df.rename(columns={"volume_m2": "volume_m2_real"}, inplace=True)

    global_metrics_df = []
    for key, df in pred_dfs.items():
        
        df = media_mensal_por_ano(
            df,
            column="volume_m2",
        )

        metrics, df_erros = calculate_metrics_regression_by_month(
            df_real=real_df,
            df_pred=df,
            col_real="volume_m2_real",
            col_pred="volume_m2",
            on=["year", "month"],
        )

        metrics['threshold'] = float(key.replace('df_volumes_trh_', ''))

        global_metrics_df.append(metrics)
        df_erros.to_csv(f"{save_path}{location_name}/volume_errors_{float(key.replace('df_volumes_trh_', ''))}.csv", index=False)


    metrics_df = pd.DataFrame(global_metrics_df)
    metrics_df.to_csv(f"{save_path}{location_name}/volume_metrics.csv", index=False)

    return True


def plot_results(
    areas_df: DataFrame,
    volumes_dfs: dict,
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

    # volumes_df = dataframe.loc[dataframe["CLOUDY_PIXEL_PERCENTAGE"] < 100]
    final_dir = f"{save_path}{location_name}/plots"

    os.makedirs(f"{final_dir}", exist_ok=True)

    logger.info(f"Saving plots to {final_dir}")

    logger.info("Plotting areas...")
    # areas_mean_df = media_mensal_por_ano(areas_df, column="m2_area")

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

    volumes_mean_dfs = {}
    for key, dataframe in volumes_dfs.items():
        volumes_mean_dfs[key] = medias_mensais_por_ano(dataframe)

    # volumes_mean_df = medias_mensais_por_ano(
        # volumes_df,
            # columns=[column for column in list(volumes_df.columns) if "volume" in column][0],
    # )

    # volumes_df = volumes_df.rename(
    #     columns={
    #         [column for column in list(volumes_df.columns) if "volume" in column][
    #             0
    #         ]: "volume_m2"
    #     }
    # )

    methods = {f"{method_name} ({float(key.replace('df_volumes_trh_', ''))*100}%)": dataframe for key, dataframe in volumes_dfs.items()}
    methods[ground_truth_name] = gound_truth_df
    volume_columns = ['volume_m2' if "%)" in key else 'volume_m2' for key in list(methods.keys())]

    figure1 = plot_series_ano_mes(
        methods,
        volume_columns=volume_columns,
        data_inicio="01/2019",
        data_fim="06/2025",
        titulo=f"{method_name} X {ground_truth_name} ao longo do tempo",
    )

    volume_columns = [ 'volume_m2_mean' if "%)" in key  else 'volume_m2' for key in list(methods.keys())]
    figure2 = plot_series_ano_mes(
        methods,
        volume_columns=volume_columns,
        data_inicio="01/2019",
        data_fim="06/2025",
        titulo=f"{method_name} X {ground_truth_name} ao longo do tempo (filtro da média)",
    )

    volume_columns = ['volume_m2_savgol' if "%)" in key else 'volume_m2' for key in list(methods.keys())]
    figure3 = plot_series_ano_mes(
        methods,
        volume_columns=volume_columns,
        data_inicio="01/2019",
        data_fim="06/2025",
        titulo=f"{method_name} X {ground_truth_name} ao longo do tempo (filtro de savgol)",
    )

    volume_columns = ['volume_m2_median' if "%)" in key else 'volume_m2' for key in list(methods.keys())]
    figure4 = plot_series_ano_mes(
        methods,
        volume_columns=volume_columns,
        data_inicio="01/2019",
        data_fim="06/2025",
        titulo=f"{method_name} X {ground_truth_name} ao longo do tempo (filtro da mediana)",
    )

    volume_columns = ['volume_m2_zscore' if "%)" in key else 'volume_m2' for key in list(methods.keys())]
    figure5 = plot_series_ano_mes(
        methods,
        data_inicio="01/2019",
        data_fim="06/2025",
        volume_columns=volume_columns,
        titulo=f"{method_name} X {ground_truth_name} ao longo do tempo (zscore)",
    )

    # Mean
    methods = {f"{method_name} ({float(key.replace('df_volumes_trh_', ''))*100}%) ": dataframe for key, dataframe in volumes_mean_dfs.items()}
    methods[ground_truth_name] = ground_truth_mean_df
    volume_columns = ['volume_m2' if "%)" in key else 'volume_m2' for key in list(methods.keys())]

    figure1_mean = plot_series_ano_mes(
        methods,
        data_inicio="01/2019",
        data_fim="06/2025",
        volume_columns=volume_columns,
        titulo=f"{method_name} X {ground_truth_name} ao longo do tempo (média mensal)",
    )

    volume_columns = ['volume_m2_mean' if "%)" in key else 'volume_m2' for key in list(methods.keys())]
    figure2_mean = plot_series_ano_mes(
        methods,
        data_inicio="01/2019",
        data_fim="06/2025",
        volume_columns=volume_columns,
        titulo=f"{method_name} X {ground_truth_name} ao longo do tempo (média mensal + filtro da média)",
    )

    volume_columns = ['volume_m2_savgol' if "%)" in key else 'volume_m2' for key in list(methods.keys())]
    figure3_mean = plot_series_ano_mes(
        methods,
        data_inicio="01/2019",
        data_fim="06/2025",
        volume_columns=volume_columns,
        titulo=f"{method_name} X {ground_truth_name} ao longo do tempo (média mensal + filtro de savgol)",
    )

    volume_columns = ['volume_m2_median' if "%)" in key else 'volume_m2' for key in list(methods.keys())]
    figure4_mean = plot_series_ano_mes(
        methods,
        data_inicio="01/2019",
        data_fim="06/2025",
        volume_columns=volume_columns,
        titulo=f"{method_name} X {ground_truth_name} ao longo do tempo (média mensal + filtro da mediana)",
    )

    volume_columns = ['volume_m2_zscore' if "%)" in key else 'volume_m2' for key in list(methods.keys())]
    figure5_mean = plot_series_ano_mes(
        methods,
        data_inicio="01/2019",
        data_fim="06/2025",
        volume_columns=volume_columns,
        titulo=f"{method_name} X {ground_truth_name} ao longo do tempo (média mensal + zscore)",
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
        f"{final_dir}/{method_name}_vs_{ground_truth_name}_ao_longo_do_tempo_z_score.png",
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
        f"{final_dir}/{method_name}_vs_{ground_truth_name}_ao_longo_do_tempo_media_zscore_filtro.png",
        bbox_inches="tight",
    )
    return True
