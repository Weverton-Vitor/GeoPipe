"""
This is a boilerplate pipeline 'unet'
generated using Kedro 0.19.12
"""

from kedro.pipeline import node, Pipeline, pipeline  # noqa
from .nodes import apply_unet

def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=apply_unet,
                inputs={
                    "toa_path": "params:configs.toa_dowload_path",
                    "location_name": "params:configs.location_name",
                    "save_masks_path": "params:configs.save_masks_path",
                    "save_plots_path": "params:configs.save_plot_masks_path",
                    "skip_masks": "params:configs.skip_masks",
                    "unet_params": "params:configs.unet",  # parâmetros específicos do Unet
                },
                outputs="unet_segmentation_output",
                name="apply_UNet",
            )
        ]
    )
