"""
This is a boilerplate pipeline 'download_and_preprocess'
generated using Kedro 0.19.10
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import (
    apply_fmask,
    create_dirs,
    donwload_images,
    shapefile2feature_collection,
)


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline([
        node(
            func=create_dirs,
            inputs={
                "dowload_path":"params:sentinel.dowload_path",
                "location_name":"params:sentinel.location_name",
                "save_masks_path": "params:sentinel.save_masks_path",
                "save_plots_path": "params:sentinel.save_plot_masks_path",
                "init_date":"params:sentinel.init_date",
                "final_date":"params:sentinel.final_date"
            },
            outputs="dependency1",
            name="create_dirs"
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
                        "collection_id":"params:sentinel.collection_id",
                        "dowload_path":"params:sentinel.dowload_path",
                        "location_name":"params:sentinel.location_name",
                        "init_date":"params:sentinel.init_date",
                        "final_date":"params:sentinel.final_date",
                        "prefix_images_name":"params:sentinel.prefix_images_name",
                        "all_bands":"params:sentinel.all_bands",
                        "scale":"params:sentinel.scale",
                        "skip_download":"params:sentinel.skip_download",
                        "roi":"shapefile_features"},
                outputs="dependency2",
                name="download_images",
            ),
         node(
            func=apply_fmask,
            inputs={
                "dependency": "dependency2",
                "toa_path": "params:sentinel.dowload_path",
                "location_name": "params:sentinel.location_name",
                "save_masks_path": "params:sentinel.save_masks_path",
                "save_plots_path": "params:sentinel.save_plot_masks_path",
                "scale_factor":"params:sentinel.scale_factor",
            },
            outputs=None,
            name="appy_FMask")
    ])
