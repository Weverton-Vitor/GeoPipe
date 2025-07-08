"""
This is a boilerplate pipeline 'calculate_spectral_indices'
generated using Kedro 0.19.10
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import (
    calculate_spectral_indices,
    create_dirs,
)


def create_pipeline(dependencies: list=["created_spectral_indice_dirs_dependency", "cloud_removed_dependency"], **kwargs) -> Pipeline:
    dependencies = {x: x for x in dependencies}
    return pipeline([
         node(
                func=create_dirs,
                inputs={
                    "spectral_indice": "params:configs.spectral_indice",
                    "spectral_index_save_path": "params:configs.spectral_index_save_path",
                    "location_name": "params:configs.location_name",
                    "init_date": "params:configs.init_date",
                    "final_date": "params:configs.final_date",
                },
                outputs="created_spectral_indice_dirs_dependency",
                name="create_spectral_indice_directories",
            ),
            node(
                func=calculate_spectral_indices,
                inputs={
                    "images_path": "params:configs.spectral_indice_target_images_paths",
                    "spectral_index_save_path": "params:configs.spectral_index_save_path",
                    "location_name": "params:configs.location_name",
                    "skip_spectral_indice": "params:configs.skip_spectral_indice",
                    "spectral_indice_name": "params:configs.spectral_indice",
                } | dependencies,
                outputs="spectral_dependency",
                name="calculate_spectral_indices",
            ),
    ])
