"""
This is a boilerplate pipeline 'deepwatermap'
generated using Kedro 0.19.10
"""

from kedro.pipeline import Pipeline, node, pipeline
from .nodes import apply_deep_water_map


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=apply_deep_water_map,
                inputs={
                    "image_path": "params:configs.clean_images_paths",
                    "save_path": "params:configs.water_masks_save_path",
                },
                outputs="dependency10",
                name="apply_deep_water_map",
            ),
        ]
    )
