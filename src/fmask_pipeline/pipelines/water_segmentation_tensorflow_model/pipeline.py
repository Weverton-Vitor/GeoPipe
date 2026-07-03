"""
This is a boilerplate pipeline 'watnet'
generated using Kedro 0.19.10
"""

from kedro.pipeline import Pipeline, node, pipeline

from fmask_pipeline.pipelines.water_segmentation_tensorflow_model.nodes import (
    apply_water_segmentation_onnx,
    create_dirs,
)


def create_pipeline(
    dependencies: list = [
        "save_water_masks_path",
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
                    "use_no_cloud_images": "params:configs.use_no_cloud_images",
                    "water_model_name": "params:configs.water_model_name",
                    "init_date": "params:configs.init_date",
                    "final_date": "params:configs.final_date",
                    "cloud_mask_algoritm": "params:configs.mask_type",
                    "reconstruction_algorithm": "params:configs.reconstruction_algorithm",
                },
                outputs="save_water_masks_path",
                name="create_deepwatermap_directories",
            ),
            node(
                func=apply_water_segmentation_onnx,
                inputs={
                    "save_path": "save_water_masks_path",
                    "location_name": "params:configs.location_name",
                    "skip_water_segmentation": "params:configs.skip_water_segmentation",
                    "threshold": "params:configs.watnet_threshold",
                    "water_model_name": "params:configs.water_model_name",
                    "patch_size": "params:configs.patch_size",
                    "cloud_mask_algoritm": "params:configs.mask_type",
                    "reconstruction_algorithm": "params:configs.reconstruction_algorithm",
                    dependencies[0]: dependencies[0],
                    dependencies[1]: dependencies[1],
                },
                outputs="water_mask_dependency",
                name="apply_Water_Segmentation_Tensorflow_Model",
            ),
        ]
    )
