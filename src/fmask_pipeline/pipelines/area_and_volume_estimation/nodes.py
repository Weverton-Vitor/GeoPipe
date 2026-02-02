import gc
import glob
import logging
import os
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

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
    process_single_mask,
)
from utils.metrics.regression import calculate_metrics_regression_by_month

logger = logging.getLogger(__name__)



def estimate_water_area(
    water_masks_path: str,
    path_shapefile: str,
    thresholds: list,
    save_path: str,
    location_name: str,
    dependency1=None,
    max_workers: int | None = None,
):

    logger.info(f"Estimating water area using {max_workers} workers...")
    # Estrutura final
    results = {
        threshold: {
            "water_masks": [],
            "year": [],
            "month": [],
            "day": [],
            "m2_area": [],
            "km2_area": [],
            "CLOUDY_PIXEL_PERCENTAGE": [],
        }
        for threshold in thresholds
    }

    masks_path = os.path.join(water_masks_path, location_name)
    save_dir = os.path.join(save_path, location_name)
    os.makedirs(save_dir, exist_ok=True)

    water_masks = glob.glob(
        os.path.join(masks_path, "**", "*.tif"),
        recursive=True
    )

    tasks = [
        (mask_path, path_shapefile, thresholds)
        for mask_path in water_masks
    ]

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_single_mask, task) for task in tasks]

        with tqdm(total=len(futures), desc="Estimate Area", unit="images") as pbar:
            for future in as_completed(futures):
                batch_results = future.result()

                for r in batch_results:
                    tr = r["threshold"]
                    results[tr]["water_masks"].append(r["water_masks"])
                    results[tr]["year"].append(r["year"])
                    results[tr]["month"].append(r["month"])
                    results[tr]["day"].append(r["day"])
                    results[tr]["m2_area"].append(r["m2_area"])
                    results[tr]["km2_area"].append(r["km2_area"])
                    results[tr]["CLOUDY_PIXEL_PERCENTAGE"].append(
                        r["CLOUDY_PIXEL_PERCENTAGE"]
                    )

                pbar.update(1)

    # ---------- DATAFRAME BUILD ----------
    thresholds_results_df = {
        f"df_areas_trh_{threshold}": pd.DataFrame(data)
        for threshold, data in results.items()
    }

    # ---------- SAVE ----------
    os.makedirs(save_dir, exist_ok=True)
    for name, df in thresholds_results_df.items():
        df.to_csv(os.path.join(save_dir, f"{name}.csv"), index=False)

    return thresholds_results_df


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

        df_volume.to_csv(
            f"{save_path}{location_name}/{key.replace('areas', 'volumes')}.csv",
            index=False,
        )
        dfs[key.replace("areas", "volumes")] = df_volume
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

        metrics["threshold"] = float(key.replace("df_volumes_trh_", ""))

        global_metrics_df.append(metrics)
        df_erros.to_csv(
            f"{save_path}{location_name}/volume_errors_{float(key.replace('df_volumes_trh_', ''))}.csv",
            index=False,
        )

    metrics_df = pd.DataFrame(global_metrics_df)
    metrics_df.to_csv(f"{save_path}{location_name}/volume_metrics.csv", index=False)

    return True

def plot_results(
    areas_df: DataFrame,
    volumes_dfs: dict,
    location_name: str,
    save_path: str,
    method_name: str,
    initial_date: str,
    end_date: str,
    ground_truth_name: str,
    ground_truth_path_df: str,
    ground_truth_column_volume: str = "Volume Útil (hm³)",
    ground_truth_column_date: str = "Data da Medição",
    raw_thresholds: bool = False,
    escale: int = 1e6,
) -> bool:
    """
    Generate and save comparison plots between estimated water volumes
    (derived from satellite imagery) and ground truth measurements.

    This function:
    - Loads and preprocesses ground truth data
    - Computes monthly statistics
    - Organizes multiple estimation methods
    - Generates time series plots with different filters
    - Saves all figures to disk

    Returns:
        bool: True if plots were successfully generated
    """

    # ======================================================
    # 1. DEFINE OUTPUT DIRECTORY
    # ======================================================
    # All plots will be saved under:
    # {save_path}/{location_name}/plots/
    final_dir = os.path.join(save_path, location_name, "plots")
    os.makedirs(final_dir, exist_ok=True)

    logger.info(f"Saving plots to {final_dir}")

    # ======================================================
    # 2. LOAD AND PREPROCESS GROUND TRUTH DATA
    # ======================================================
    # Load CSV containing in-situ or official measurements
    gt_df = pd.read_csv(ground_truth_path_df)

    # Extract year and month from the measurement date column
    # Assumes date format like: DD/MM/YYYY
    gt_df["year"] = gt_df[ground_truth_column_date].str.split("/").str[-1]
    gt_df["month"] = gt_df[ground_truth_column_date].str.split("/").str[-2]

    # Convert volume column to float
    # Handles decimal commas used in Brazilian datasets
    gt_df[ground_truth_column_volume] = (
        gt_df[ground_truth_column_volume]
        .astype(str)
        .str.replace(",", ".")
        .astype(float)
    )

    # Convert volume from hm³ to m² (scaled if necessary)
    # 1 hm³ = 1,000,000 m³
    gt_df["volume_m2"] = gt_df[ground_truth_column_volume] * 1_000_000 / escale

    # Compute monthly mean values for ground truth
    gt_mean_df = media_mensal_por_ano(
        gt_df,
        column="volume_m2",
    )

    # ======================================================
    # 3. COMPUTE MONTHLY MEANS FOR ESTIMATED VOLUMES
    # ======================================================
    # Each entry in volumes_dfs corresponds to a threshold/method
    volumes_mean_dfs = {
        key: medias_mensais_por_ano(df)
        for key, df in volumes_dfs.items()
    }

    # ======================================================
    # 4. HELPER FUNCTION TO BUILD METHODS DICTIONARY
    # ======================================================
    # This function creates a dictionary like:
    # {
    #   "Method (30%)": dataframe,
    #   "Method (40%)": dataframe,
    #   "Ground Truth": dataframe
    # }
    def build_methods(dataframes: dict, include_ground_truth=True):
        methods = {}

        for key, df in dataframes.items():
            # Extract numeric threshold from key name
            threshold = key.replace("df_volumes_trh_", "")

            # Format label depending on configuration
            # TODO adapt to ndwi e mndwi thresholds
            label = (
                f"{method_name} ({float(threshold) * 100}%)"
                if not raw_thresholds
                else f"{method_name} ({threshold})"
            )

            methods[label] = df

        # Optionally append ground truth to the comparison
        if include_ground_truth:
            methods[ground_truth_name] = gt_df

        return methods

    # ======================================================
    # 5. PLOT CONFIGURATION
    # ======================================================
    # Each tuple defines:
    # (column to plot, filename suffix)
    plot_configs = [
        ("volume_m2", "ao_longo_do_tempo"),
        ("volume_m2_mean", "filtro_da_media"),
        ("volume_m2_savgol", "filtro_da_savgol"),
        ("volume_m2_median", "filtro_da_mediana"),
        ("volume_m2_zscore", "z_score"),
    ]

    # Store all figures and filenames before saving
    figures = []

    # ======================================================
    # 6. GENERATE RAW TIME SERIES PLOTS
    # ======================================================
    methods = build_methods(volumes_dfs)

    for column, suffix in plot_configs:
        # Ground truth always uses raw "volume_m2"
        # Estimated methods may use filtered columns
        volume_columns = [
            column if method_name in key else "volume_m2"
            for key in methods.keys()
        ]

        fig = plot_series_ano_mes(
            methods,
            volume_columns=volume_columns,
            data_inicio=initial_date,
            data_fim=end_date,
            titulo=f"{method_name} X {ground_truth_name} ({suffix})",
        )

        figures.append(
            (fig, f"{method_name}_vs_{ground_truth_name}_{suffix}.png")
        )

    # ======================================================
    # 7. GENERATE MONTHLY MEAN PLOTS
    # ======================================================
    methods_mean = build_methods(volumes_mean_dfs)

    # Replace raw ground truth with its monthly mean version
    methods_mean[ground_truth_name] = gt_mean_df

    for column, suffix in plot_configs:
        volume_columns = [
            column if method_name in key else "volume_m2"
            for key in methods_mean.keys()
        ]

        fig = plot_series_ano_mes(
            methods_mean,
            volume_columns=volume_columns,
            data_inicio=initial_date,
            data_fim=end_date,
            titulo=f"{method_name} X {ground_truth_name} (média mensal + {suffix})",
        )

        figures.append(
            (fig, f"{method_name}_vs_{ground_truth_name}_media_{suffix}.png")
        )

    # ======================================================
    # 8. SAVE ALL GENERATED FIGURES
    # ======================================================
    for fig, filename in figures:
        fig.savefig(
            os.path.join(final_dir, filename),
            bbox_inches="tight",
        )

    logger.info("All plots generated successfully.")
    return True
