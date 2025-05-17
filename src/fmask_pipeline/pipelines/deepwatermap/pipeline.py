"""
This is a boilerplate pipeline 'deepwatermap'
generated using Kedro 0.19.10
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import apply_deep_water_map, create_dirs


def create_pipeline(dependencies: list=["created_deep_water_map_dirs_dependency", "cloud_removed_dependency"], **kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=create_dirs,
                inputs={
                    "water_masks_save_path": "params:configs.water_masks_save_path",
                    "location_name": "params:configs.location_name",
                    "init_date": "params:configs.init_date",
                    "final_date": "params:configs.final_date",
                },
                outputs="created_deep_water_map_dirs_dependency",
                name="create_deepwatermap_directories",
            ),
            node(
                func=apply_deep_water_map,
                inputs={
                    "images_path": "params:configs.clean_images_paths",
                    "water_masks_save_path": "params:configs.water_masks_save_path",
                    "location_name": "params:configs.location_name",
                    "scale_factor": "params:configs.scale_factor",
                    "offset": "params:configs.offset",
                    "skip_deepewatermap": "params:configs.skip_deepewatermap",
                    "threshold": "params:configs.deepwatermap_threshold",
                    dependencies[0]: dependencies[0],
                    dependencies[1]: dependencies[1],
                },
                outputs="water_mask_dependency",
                name="apply_deep_water_map",
            ),
        ]
    )
