import glob
import logging
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
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
    process_single_mask,
)
from utils.metrics.regression import (
    calculate_metrics_regression,
)

import os
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

logger = logging.getLogger(__name__)


def estimate_water_area(
    water_masks_path: str,
    path_shapefile: str,
    thresholds: list,
    save_path: str,
    location_name: str,
    reconstruction_algorithm: str,
    cloud_mask_algoritm: str,
    model_path: str,
    dependency1=None,
    max_workers: int | None = None,
):
    logger.info(f"Estimating water area using {max_workers} workers...")

    water_segmentation_algorithm = model_path.split("/")[-1].split(".")[0]

    masks_path = os.path.join(
        water_masks_path,
        location_name,
        cloud_mask_algoritm,
        reconstruction_algorithm,
        water_segmentation_algorithm,
    )
    save_dir = os.path.join(
        save_path,
        location_name,
        cloud_mask_algoritm,
        reconstruction_algorithm,
        water_segmentation_algorithm,
    )
    os.makedirs(save_dir, exist_ok=True)

    water_masks = glob.glob(
        os.path.join(masks_path, "**", "*.tif"),
        recursive=True,
    )

    tasks = [(mask_path, path_shapefile, thresholds) for mask_path in water_masks]

    # Lista única para armazenar todos os resultados
    results = []

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_single_mask, task) for task in tasks]

        with tqdm(
            total=len(futures),
            desc="Estimate Area",
            unit="images",
        ) as pbar:
            for future in as_completed(futures):
                batch_results = future.result()

                # Cada item de batch_results deve conter a chave "threshold"
                results.extend(batch_results)

                pbar.update(1)

    # ---------- DATAFRAME BUILD ----------
    results_df = pd.DataFrame(results)

    # Opcional: ordenar para facilitar análises futuras
    if not results_df.empty:
        results_df = results_df.sort_values(
            by=["threshold", "year", "month", "day"]
        ).reset_index(drop=True)

    # ---------- SAVE ----------
    csv_path = os.path.join(save_dir, "water_areas.csv")
    results_df.to_csv(csv_path, index=False)

    return results_df



def estimate_water_volume(
    water_areas_df: pd.DataFrame,
    cav_path: str,
    save_path: str,
    location_name: str,
    thresholds: list,
    reconstruction_algorithm: str,
    cloud_mask_algoritm: str,
    model_path: str,
    cav_area_column: str = "area",
    cav_volume_column: str = "volume",
    year_column: str = "year",
    month_column: str = "month",
    cloud_percentage_column: str = "CLOUDY_PIXEL_PERCENTAGE",
    areas_columns: list = None,
    escale: float = 1,
    max_workers: int = None,
) -> pd.DataFrame:
    """
    Calcula volumes para múltiplos thresholds e salva um único arquivo.

    Returns
    -------
    pd.DataFrame
        DataFrame consolidado contendo todos os thresholds.
    """

    if areas_columns is None:
        areas_columns = []

    
    # Pegando o tipo de cada threshold (se disponível) para usar na construção dos labels
    threshold_df = water_areas_df[["threshold", "threshold_type"]].drop_duplicates()

    threshold_types = threshold_df['threshold_type'].to_list()
    thresholds = threshold_df['threshold'].to_list()
    
    df_cav = pd.read_csv(cav_path)

    def process_threshold(threshold):
        threshold_type = threshold[1]
        threshold = threshold[0]
        df_threshold = water_areas_df.loc[
            water_areas_df["threshold"] == threshold
        ].copy()

        if df_threshold.empty:
            return None

        df_volume = calculate_volumes_to_multiple_methods(
            df_areas=df_threshold,
            df_cav=df_cav,
            cav_area_column=cav_area_column,
            cav_volume_column=cav_volume_column,
            year_column=year_column,
            month_column=month_column,
            cloud_percentage_column=cloud_percentage_column,
            areas_columns=areas_columns,
            escale=escale,
        )

        df_volume["threshold"] = threshold
        df_volume["threshold_type"] = threshold_type

        return df_volume

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_threshold, zip(thresholds, threshold_types)))

    results = [df for df in results if df is not None]

    if not results:
        return pd.DataFrame()

    final_df = pd.concat(results, ignore_index=True)

    water_segmentation_algorithm = model_path.split("/")[-1].split(".")[0]

    save_dir = os.path.join(
        save_path,
        location_name,
        cloud_mask_algoritm,
        reconstruction_algorithm,
        water_segmentation_algorithm,
    )
    os.makedirs(save_dir, exist_ok=True)

    output_file = os.path.join(save_dir, "water_volumes.csv")

    final_df.to_csv(output_file, index=False)

    return final_df


def calculate_metrics(
    path_real_df: str,
    pred_df: pd.DataFrame,
    save_path: str,
    col_real: str,
    location_name: str,
    reconstruction_algorithm: str,
    cloud_mask_algoritm: str,
    model_path: str,
    max_workers: int = None,
) -> bool:

    logger.info("Calculating metrics")

    real_df = pd.read_csv(path_real_df)

    real_df["day"] = real_df["Data da Medição"].str.split("/").str[0]
    real_df["year"] = real_df["Data da Medição"].str.split("/").str[-1]
    real_df["month"] = real_df["Data da Medição"].str.split("/").str[-2]


    real_df["Volume Útil (hm³)"] = pd.to_numeric(
        real_df["Volume Útil (hm³)"].astype(str).str.replace(",", "."),
        errors="coerce",
    )

    real_df["volume_m2_real"] = real_df["Volume Útil (hm³)"]

    real_df.rename(
        columns={"volume_m2": "volume_m2_real"},
        inplace=True,
    )
    
    pred_df["experiment"] = np.where(
    pred_df["threshold_type"] == "otsu",
        "otsu",
        "fixed_" + pred_df["threshold"].astype(str)
    )

    experiments = pred_df["experiment"].unique()

    def process_experiment(experiment):

        df_exp = pred_df.loc[
            pred_df["experiment"] == experiment
        ].copy()

        metrics, df_errors = calculate_metrics_regression(
            df_real=real_df,
            df_pred=df_exp,
            col_real="volume_m2_real",
            col_pred="volume_m2",
            on=["year", "month", "day"],
        )

        if experiment == "otsu":
            metrics["threshold"] = "otsu"
        else:
            metrics["experiment"] = df_exp["threshold"].iloc[0]
            df_errors["threshold"] = df_exp["threshold"].iloc[0]

        # opcional
        if experiment == "otsu":
            metrics["threshold"] = np.nan
        else:
            metrics["threshold"] = float(
                experiment.replace("fixed_", "")
            )

        return metrics, df_errors

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(
            executor.map(
                process_experiment,
                experiments
            )
        )

    metrics_list = []
    errors_list = []

    for metrics, errors in results:
        metrics_list.append(metrics)
        errors_list.append(errors)

    metrics_df = pd.DataFrame(metrics_list)
    errors_df = pd.concat(errors_list, ignore_index=True)

    water_segmentation_algorithm = model_path.split("/")[-1].split(".")[0]
    output_dir = os.path.join(
        save_path,
        location_name,
        cloud_mask_algoritm,
        reconstruction_algorithm,
        water_segmentation_algorithm,
    )

    os.makedirs(output_dir, exist_ok=True)

    metrics_df.to_csv(
        f"{output_dir}/volume_metrics.csv",
        index=False,
    )

    errors_df.to_csv(
        f"{output_dir}/volume_errors.csv",
        index=False,
    )

    return True


import os
from pathlib import Path

import pandas as pd
from pandas import DataFrame


def plot_results(
    areas_df: DataFrame,
    volumes_df: DataFrame,
    location_name: str,
    save_path: str,
    method_name: str,
    initial_date: str,
    end_date: str,
    ground_truth_name: str,
    ground_truth_path_df: str,
    reconstruction_algorithm: str,
    cloud_mask_algoritm: str,
    model_path: str,
    ground_truth_column_volume: str = "Volume Útil (hm³)",
    ground_truth_column_date: str = "Data da Medição",
    raw_thresholds: bool = False,
    escale: int = 1e6,
) -> bool:
    """
    Generate and save comparison plots between estimated water volumes
    and ground truth measurements.

    Expected volumes_df structure:
        year | month | volume_m2 | threshold | ...
    """

    # ======================================================
    # 1. DEFINE OUTPUT DIRECTORY
    # ======================================================

    water_segmentation_algorithm = Path(model_path).stem

    final_dir = os.path.join(
        save_path,
        location_name,
        cloud_mask_algoritm,
        reconstruction_algorithm,
        water_segmentation_algorithm,
        "plots",
    )

    os.makedirs(final_dir, exist_ok=True)

    logger.info(f"Saving plots to {final_dir}")

    # ======================================================
    # 2. LOAD AND PREPROCESS GROUND TRUTH DATA
    # ======================================================

    gt_df = pd.read_csv(ground_truth_path_df)

    dates = pd.to_datetime(
        gt_df[ground_truth_column_date],
        format="%d/%m/%Y",
    )

    gt_df["year"] = dates.dt.year
    gt_df["month"] = dates.dt.month

    gt_df[ground_truth_column_volume] = pd.to_numeric(
        gt_df[ground_truth_column_volume].astype(str).str.replace(",", "."),
        errors="coerce",
    )

    gt_df["volume_m2"] = gt_df[ground_truth_column_volume] * 1_000_000 / escale

    gt_mean_df = media_mensal_por_ano(
        gt_df,
        column="volume_m2",
    )

    # ======================================================
    # 3. SPLIT ESTIMATED DATA BY THRESHOLD
    # ======================================================

    grouped_thresholds = {
        threshold: df.copy() for threshold, df in volumes_df.groupby("threshold")
    }

    # ======================================================
    # 4. COMPUTE MONTHLY MEANS
    # ======================================================

    volumes_mean_dfs = {
        threshold: medias_mensais_por_ano(df)
        for threshold, df in grouped_thresholds.items()
    }

    # ======================================================
    # 5. HELPER FUNCTION
    # ======================================================

    def build_methods(
        dataframes: dict,
        include_ground_truth: bool = True,
        ground_truth_df: DataFrame = None,
    ) -> dict:

        methods = {}

        for threshold, df in sorted(dataframes.items()):
            label = (
                f"{method_name} ({float(threshold) * 100:.0f}%)"
                if not raw_thresholds
                else f"{method_name} ({threshold})"
            )

            methods[label] = df

        if include_ground_truth and ground_truth_df is not None:
            methods[ground_truth_name] = ground_truth_df

        return methods

    # ======================================================
    # 6. PLOT CONFIGURATION
    # ======================================================

    plot_configs = [
        ("volume_m2", "ao_longo_do_tempo"),
        ("volume_m2_mean", "filtro_da_media"),
        ("volume_m2_savgol", "filtro_da_savgol"),
        ("volume_m2_median", "filtro_da_mediana"),
        ("volume_m2_zscore", "z_score"),
    ]

    figures = []

    # ======================================================
    # 7. RAW SERIES PLOTS
    # ======================================================

    methods = build_methods(
        grouped_thresholds,
        include_ground_truth=True,
        ground_truth_df=gt_df,
    )

    for column, suffix in plot_configs:
        volume_columns = [
            column if key != ground_truth_name else "volume_m2"
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
            (
                fig,
                f"{method_name}_vs_{ground_truth_name}_{suffix}.png",
            )
        )

    # ======================================================
    # 8. MONTHLY MEAN PLOTS
    # ======================================================

    methods_mean = build_methods(
        volumes_mean_dfs,
        include_ground_truth=True,
        ground_truth_df=gt_mean_df,
    )

    for column, suffix in plot_configs:
        volume_columns = [
            column if key != ground_truth_name else "volume_m2"
            for key in methods_mean.keys()
        ]

        fig = plot_series_ano_mes(
            methods_mean,
            volume_columns=volume_columns,
            data_inicio=initial_date,
            data_fim=end_date,
            titulo=(f"{method_name} X {ground_truth_name} (média mensal + {suffix})"),
        )

        figures.append(
            (
                fig,
                f"{method_name}_vs_{ground_truth_name}_media_{suffix}.png",
            )
        )

    # ======================================================
    # 9. SAVE FIGURES
    # ======================================================

    for fig, filename in figures:
        fig.savefig(
            os.path.join(final_dir, filename),
            bbox_inches="tight",
        )

    logger.info("All plots generated successfully.")

    return True
