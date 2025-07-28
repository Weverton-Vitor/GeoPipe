"""
This is a boilerplate pipeline 'watnet'
generated using Kedro 0.19.10
"""

from kedro.pipeline import Pipeline, pipeline, node

from fmask_pipeline.pipelines.watnet.nodes import apply_watnet, create_dirs


def create_pipeline(
    dependencies: list = [
        "created_watnet_dirs_dependency",
        "cloud_removed_dependency",
    ],
    **kwargs,
) -> Pipeline:
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
                outputs="created_watnet_dirs_dependency",
                name="create_deepwatermap_directories",
            ),
            node(
                func=apply_watnet,
                inputs={
                    "images_path": "params:configs.images_paths",
                    "water_masks_save_path": "params:configs.watnet_masks_save_path",
                    "location_name": "params:configs.location_name",
                    "skip_watnet": "params:configs.skip_watnet",
                    "threshold": "params:configs.watnet_threshold",
                    dependencies[0]: dependencies[0],
                    dependencies[1]: dependencies[1],
                },
                outputs="water_mask_dependency",
                name="apply_WatNet",
            ),
        ]
    )
