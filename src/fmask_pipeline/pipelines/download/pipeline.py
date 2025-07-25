"""
This is a boilerplate pipeline 'download_and_preprocess'
generated using Kedro 0.19.10
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import (
    create_dirs,
    donwload_images,
    shapefile2feature_collection,
)


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=create_dirs,
                inputs={
                    "toa_dowload_path": "params:configs.toa_dowload_path",
                    "boa_dowload_path": "params:configs.boa_dowload_path",
                    "location_name": "params:configs.location_name",
                    "save_masks_path": "params:configs.save_masks_path",
                    "save_plots_path": "params:configs.save_plot_masks_path",
                    "save_clean_images_path": "params:configs.save_clean_images_path",
                    "cloud_removal_log": "params:configs.cloud_removal_log",
                    "init_date": "params:configs.init_date",
                    "final_date": "params:configs.final_date",
                },
                outputs="created_dirs_dependency",
                name="create_download_and_preprocess_directories",
            ),
            node(
                func=shapefile2feature_collection,
                inputs=["shapefile"],
                outputs="shapefile_features",
                name="load_shapefile",
            ),
            node(
                func=donwload_images,
                inputs={
                    "created_dirs_dependency": "created_dirs_dependency",
                    "collection_ids": "params:configs.toa_collection_ids",
                    "dowload_path": "params:configs.toa_dowload_path",
                    "save_metadata": "params:configs.save_metadata",
                    "location_name": "params:configs.location_name",
                    "init_date": "params:configs.init_date",
                    "final_date": "params:configs.final_date",
                    "prefix_images_name": "params:configs.toa_prefix_images_name",
                    "selected_bands": "params:configs.selected_bands",
                    "scale": "params:configs.scale",
                    "skip_download": "params:configs.toa_skip_download",
                    "roi": "shapefile_features",
                },
                outputs="TOA_download_images_dependency",
                name="download_TOA_images",
            ),
            node(
                func=donwload_images,
                inputs={
                    "created_dirs_dependency": "created_dirs_dependency",
                    "collection_ids": "params:configs.boa_collection_ids",
                    "dowload_path": "params:configs.boa_dowload_path",
                    "save_metadata": "params:configs.save_metadata",
                    "location_name": "params:configs.location_name",
                    "init_date": "params:configs.init_date",
                    "final_date": "params:configs.final_date",
                    "prefix_images_name": "params:configs.boa_prefix_images_name",
                    "selected_bands": "params:configs.selected_bands",
                    "scale": "params:configs.scale",
                    "skip_download": "params:configs.boa_skip_download",
                    "roi": "shapefile_features",
                },
                outputs="BOA_download_images_dependency",
                name="download_BOA_images",
            ),
        ]
    )
