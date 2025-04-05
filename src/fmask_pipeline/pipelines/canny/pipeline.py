"""
This is a boilerplate pipeline 'canny'
generated using Kedro 0.19.10
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import apply_canny, create_dirs


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=create_dirs,
                inputs={
                    "canny_output_save_path": "params:configs.canny_output_save_path",
                    "location_name": "params:configs.location_name",
                    "init_date": "params:configs.init_date",
                    "final_date": "params:configs.final_date",
                },
                outputs="created_canny_dirs_dependency",
                name="create_canny_directories",
            ),
            node(
                func=apply_canny,
                inputs={
                    "images_path": "params:configs.water_mask_path",
                    "canny_output_save_path": "params:configs.canny_output_save_path",
                    "location_name": "params:configs.location_name",
                    "sigma":"params:configs.sigma",
                    "lower_factor":"params:configs.lower_factor",
                    "upper_factor":"params:configs.upper_factor",
                    "water_mask_dependency": "water_mask_dependency",
                    "created_canny_dirs_dependency": "created_canny_dirs_dependency",
                },
                outputs="canny_edge_dependency",
                name="apply_canny",
            ),
        ]
    )
