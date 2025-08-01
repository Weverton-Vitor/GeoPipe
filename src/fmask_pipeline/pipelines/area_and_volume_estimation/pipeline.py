from kedro.pipeline import Pipeline, node, pipeline

from .nodes import calculate_metrics, estimate_water_area, estimate_water_volume, plot_results


def create_pipeline(dependencies=['water_mask_dependency'], **kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=estimate_water_area,
                inputs={
                    "water_masks_path": "params:configs.water_masks_path",
                    "save_path": "params:configs.area_and_volune_save_path",
                    "path_shapefile": "params:configs.path_shapefile",
                    "location_name": "params:configs.location_name",
                    "thresholds": "params:configs.thresholds",
                    "dependency1": dependencies[0],
                },
                outputs="water_areas_dfs",
                name="Estimate_Water_Area",
            ),
            node(
                func=estimate_water_volume,
                inputs={
                    "water_areas_dfs": "water_areas_dfs",
                    "cav_path": "params:configs.cav_path",
                    "cav_area_column": "params:configs.cav_area_column",
                    "cav_volume_column": "params:configs.cav_volume_column",
                    "save_path": "params:configs.area_and_volune_save_path",
                    "year_column": "params:configs.year_column",
                    "month_column": "params:configs.month_column",
                    "cloud_percentage_column": "params:configs.cloud_percentage_column",
                    "areas_columns": "params:configs.areas_columns",
                    "location_name": "params:configs.location_name",
                    "escale": "params:configs.escale",
                },
                outputs="water_volumes_dfs",
                name="Estimate_Water_Volume",
            ),
            node(
                func=calculate_metrics,
                inputs={
                    "path_real_df": "params:configs.ground_truth_path_df",
                    "pred_dfs": "water_volumes_dfs",
                    "save_path": "params:configs.area_and_volune_save_path",
                    "col_real": "params:configs.ground_truth_column_volume",
                    "location_name": "params:configs.location_name",
                },
                outputs="metrics_df",
                name="Calculate_Metrics",
            ),
            node(
                func=plot_results,
                inputs={
                    "areas_df": "water_areas_dfs",
                    "volumes_dfs": "water_volumes_dfs",
                    "save_path": "params:configs.area_and_volune_save_path",
                    "method_name": "params:configs.method_name",
                    "ground_truth_name": "params:configs.ground_truth_name",
                    "ground_truth_path_df": "params:configs.ground_truth_path_df",
                    "ground_truth_column_volume": "params:configs.ground_truth_column_volume",
                    "ground_truth_column_date": "params:configs.ground_truth_column_date",
                    "location_name": "params:configs.location_name",
                    "escale": "params:configs.escale",
                },
                outputs="plot_results",
                name="Plot_Results",
            ),
        ]
    )
