"""
This is a boilerplate pipeline 'download_and_preprocess'
generated using Kedro 0.19.10
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import (
    apply_fmask,
    cloud_removal,
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
                    "init_date": "params:configs.init_date",
                    "final_date": "params:configs.final_date",
                },
                outputs="dependency1",
                name="create_dirs",
            ),
            node(
                func=shapefile2feature_collection,
                inputs=["shapefile", "dependency1"],
                outputs="shapefile_features",
                name="load_shapefile",
            ),
            node(
                func=donwload_images,
                inputs={
                    "collection_ids": "params:configs.toa_collection_ids",
                    "dowload_path": "params:configs.toa_dowload_path",
                    "location_name": "params:configs.location_name",
                    "init_date": "params:configs.init_date",
                    "final_date": "params:configs.final_date",
                    "prefix_images_name": "params:configs.toa_prefix_images_name",
                    "selected_bands": "params:configs.selected_bands",
                    "scale": "params:configs.scale",
                    "skip_download": "params:configs.toa_skip_download",
                    "roi": "shapefile_features",
                },
                outputs="dependency2",
                name="download_TOA_images",
            ),
            node(
                func=donwload_images,
                inputs={
                    "collection_ids": "params:configs.boa_collection_ids",
                    "dowload_path": "params:configs.boa_dowload_path",
                    "location_name": "params:configs.location_name",
                    "init_date": "params:configs.init_date",
                    "final_date": "params:configs.final_date",
                    "prefix_images_name": "params:configs.boa_prefix_images_name",
                    "selected_bands": "params:configs.selected_bands",
                    "scale": "params:configs.scale",
                    "skip_download": "params:configs.boa_skip_download",
                    "roi": "shapefile_features",
                },
                outputs="dependency3",
                name="download_BOA_images",
            ),
            node(
                func=apply_fmask,
                inputs={
                    "dependency": "dependency2",
                    "dependency2": "dependency3",
                    "toa_path": "params:configs.toa_dowload_path",
                    "location_name": "params:configs.location_name",
                    "save_masks_path": "params:configs.save_masks_path",
                    "save_plots_path": "params:configs.save_plot_masks_path",
                    "scale_factor": "params:configs.scale_factor",
                    "skip_masks": "params:configs.skip_masks",
                },
                outputs="dependency4",
                name="appy_FMask",
            ),
            node(
                func=cloud_removal,
                inputs={
                    "dependency": "dependency4",
                    "path_images": "params:configs.boa_dowload_path",
                    "path_masks": "params:configs.save_masks_path",
                    "output_path": "params:configs.save_clean_images_path",
                    "location_name": "params:configs.location_name",
                    "cloud_and_cloud_shadow_pixels": "params:configs.cloud_and_cloud_shadow_pixels",
                    "init_date": "params:configs.init_date",
                    "final_date": "params:configs.final_date",
                },
                outputs="dependency5",
                name="Cloud_removal",
            ),
        ]
    )
