"""
This is a boilerplate pipeline 'download_and_preprocess'
generated using Kedro 0.19.10
"""

from kedro.pipeline import Pipeline, node, pipeline
from .nodes import donwload_images, shapefile2feature_collection

def create_pipeline(**kwargs) -> Pipeline:
    return pipeline([
        node(
                func=shapefile2feature_collection,
                inputs=["shapefile"],
                outputs="shapefile_features",
                name="load_shuttles_to_csv_node",
            ),
         node(
                func=donwload_images,
                inputs="shapefile_features",
                outputs="shuttles@csv",
                name="load_shuttles_to_csv_node",
            ),
    ])
