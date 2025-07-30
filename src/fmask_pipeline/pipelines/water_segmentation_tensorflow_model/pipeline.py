"""
This is a boilerplate pipeline 'watnet'
generated using Kedro 0.19.10
"""

from kedro.pipeline import Pipeline, node, pipeline

from fmask_pipeline.pipelines.water_segmentation_tensorflow_model.nodes import (
    apply_water_segmentation_tensorflow_model,
)
from fmask_pipeline.pipelines.watnet.nodes import create_dirs


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
                func=apply_water_segmentation_tensorflow_model,
                inputs={
                    "tensorflow_model_images_paths": "params:configs.tensorflow_model_images_paths",
                    "water_masks_save_path": "params:configs.tensorflow_model_masks_save_path",
                    "location_name": "params:configs.location_name",
                    "skip_tensorflow_model": "params:configs.skip_tensorflow_model",
                    "threshold": "params:configs.watnet_threshold",
                    "model_path": "params:configs.model_path",
                    "patch_size": "params:configs.patch_size",
                    dependencies[0]: dependencies[0],
                    dependencies[1]: dependencies[1],
                },
                outputs="water_mask_dependency",
                name="apply_Water_Segmentation_Tensorflow_Model",
            ),
        ]
    )
