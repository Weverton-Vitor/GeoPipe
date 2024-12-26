"""
This is a boilerplate pipeline 'download_and_preprocess'
generated using Kedro 0.19.10
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import apply_fmask, donwload_images, shapefile2feature_collection, create_dirs


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline([
        node(
            func=create_dirs,
            inputs={
                "dowload_path":"params:sentinel.dowload_path",
                "save_masks_path": "params:sentinel.save_masks_path",
                "save_plots_path": "params:sentinel.save_plot_masks_path",
                "init_date":"params:sentinel.init_date",
                "final_date":"params:sentinel.final_date"
            },
            outputs=[],
            name="create_dirs"
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
                        "collection_id":"params:sentinel.collection_id",
                        "dowload_path":"params:sentinel.dowload_path",
                        "init_date":"params:sentinel.init_date",
                        "final_date":"params:sentinel.final_date",
                        "prefix_images_name":"params:sentinel.prefix_images_name",
                        "all_bands":"params:sentinel.all_bands",
                        "scale":"params:sentinel.scale",
                        "roi":"shapefile_features"},
                outputs=[],
                name="download_images",
            ),
         node(
            func=apply_fmask,
            inputs={
                "toa_path": "params:sentinel.dowload_path",
                "save_masks_path": "params:sentinel.save_masks_path",
                "save_plots_path": "params:sentinel.save_plot_masks_path",
            },
            outputs=[],
            name="appy_FMask")
    ])
