from kedro.pipeline import Pipeline, node, pipeline

from .nodes import calculate_metrics, estimate_water_area, estimate_water_volume, plot_results


def create_pipeline(dependencies=['water_mask_dependency'], **kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=estimate_water_area,
                inputs={
                    "water_masks_save_path": "params:paths.water_masks_save_path",
                    "save_path": "params:paths.area_and_volume_save_path",
                    "location_name": "params:configs.location_name",
                    "max_workers": "params:configs.max_workers",
                    "cloud_mask_algoritm": "params:configs.cloud_mask_algoritm",
                    "reconstruction_algorithm": "params:configs.reconstruction_algorithm",
                    "water_model_name": "params:configs.water_model_name",
                    "dependency1": dependencies[0],
                },
                outputs="water_areas_df",
                name="Estimate_Water_Area",
            ),
            node(
                func=estimate_water_volume,
                inputs={
                    "water_areas_df": "water_areas_df",
                    "water_model_name": "params:configs.water_model_name",
                    "cav_area_column": "params:configs.cav_area_column",
                    "cav_volume_column": "params:configs.cav_volume_column",
                    "save_path": "params:paths.area_and_volume_save_path",
                    "year_column": "params:configs.year_column",
                    "month_column": "params:configs.month_column",
                    "cloud_percentage_column": "params:configs.cloud_percentage_column",
                    "areas_columns": "params:configs.areas_columns",
                    "location_name": "params:configs.location_name",
                    "cloud_mask_algoritm": "params:configs.cloud_mask_algoritm",
                    "reconstruction_algorithm": "params:configs.reconstruction_algorithm",
                    "max_workers": "params:configs.max_workers",
                    "escale": "params:configs.escale",
                },
                outputs="water_volumes_df",
                name="Estimate_Water_Volume",
            ),
            node(
                func=calculate_metrics,
                inputs={
                    "pred_df": "water_volumes_df",
                    "save_path": "params:paths.area_and_volume_save_path",
                    "col_real": "params:configs.ground_truth_column_volume",
                    "location_name": "params:configs.location_name",
                    "cloud_mask_algoritm": "params:configs.cloud_mask_algoritm",
                    "reconstruction_algorithm": "params:configs.reconstruction_algorithm",
                    "water_model_name": "params:configs.water_model_name",
                    "max_workers": "params:configs.max_workers",
                },
                outputs="metrics_df",
                name="Calculate_Metrics",
            ),
            node(
                func=plot_results,
                inputs={
                    "areas_df": "water_areas_df",
                    "volumes_df": "water_volumes_df",
                    "save_path": "params:paths.area_and_volume_save_path",
                    "water_model_name": "params:configs.water_model_name",
                    "initial_date": "params:configs.initial_date",
                    "end_date": "params:configs.end_date",
                    "ground_truth_name": "params:configs.ground_truth_name",
                    "ground_truth_column_volume": "params:configs.ground_truth_column_volume",
                    "ground_truth_column_date": "params:configs.ground_truth_column_date",
                    "location_name": "params:configs.location_name",
                    "raw_thresholds": "params:configs.raw_thresholds",
                    "escale": "params:configs.escale",
                    "cloud_mask_algoritm": "params:configs.cloud_mask_algoritm",
                    "reconstruction_algorithm": "params:configs.reconstruction_algorithm",
                },
                outputs="plot_results",
                name="Plot_Results",
            ),
        ]
    )
