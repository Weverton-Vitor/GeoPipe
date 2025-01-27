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
                    "toa_dowload_path": "params:sentinel.toa_dowload_path",
                    "boa_dowload_path": "params:sentinel.boa_dowload_path",
                    "location_name": "params:sentinel.location_name",
                    "save_masks_path": "params:sentinel.save_masks_path",
                    "save_plots_path": "params:sentinel.save_plot_masks_path",
                    "save_clean_images_path": "params:sentinel.save_clean_images_path",
                    "init_date": "params:sentinel.init_date",
                    "final_date": "params:sentinel.final_date",
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
                    "collection_id": "params:sentinel.toa_collection_id",
                    "dowload_path": "params:sentinel.toa_dowload_path",
                    "location_name": "params:sentinel.location_name",
                    "init_date": "params:sentinel.init_date",
                    "final_date": "params:sentinel.final_date",
                    "prefix_images_name": "params:sentinel.toa_prefix_images_name",
                    "selected_bands": "params:sentinel.selected_bands",
                    "scale": "params:sentinel.scale",
                    "skip_download": "params:sentinel.toa_skip_download",
                    "roi": "shapefile_features",
                },
                outputs="dependency2",
                name="download_TOA_images",
            ),
            node(
                func=donwload_images,
                inputs={
                    "collection_id": "params:sentinel.boa_collection_id",
                    "dowload_path": "params:sentinel.boa_dowload_path",
                    "location_name": "params:sentinel.location_name",
                    "init_date": "params:sentinel.init_date",
                    "final_date": "params:sentinel.final_date",
                    "prefix_images_name": "params:sentinel.boa_prefix_images_name",
                    "selected_bands": "params:sentinel.selected_bands",
                    "scale": "params:sentinel.scale",
                    "skip_download": "params:sentinel.boa_skip_download",
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
                    "toa_path": "params:sentinel.toa_dowload_path",
                    "location_name": "params:sentinel.location_name",
                    "save_masks_path": "params:sentinel.save_masks_path",
                    "save_plots_path": "params:sentinel.save_plot_masks_path",
                    "scale_factor": "params:sentinel.scale_factor",
                    "skip_masks": "params:sentinel.skip_masks",
                },
                outputs="dependency4",
                name="appy_FMask",
            ),
            node(
                func=cloud_removal,
                inputs={
                    "dependency": "dependency4",
                    "path_images": "params:sentinel.boa_dowload_path",
                    "path_masks": "params:sentinel.save_masks_path",
                    "output_path": "params:sentinel.save_clean_images_path",
                    "location_name": "params:sentinel.location_name",
                    "cloud_and_cloud_shadow_pixels": "params:sentinel.cloud_and_cloud_shadow_pixels",
                    "init_date": "params:sentinel.init_date",
                    "final_date": "params:sentinel.final_date",
                },
                outputs=None,
                name="Cloud_removal",
            ),
        ]
    )
