"""
This is a boilerplate pipeline 'cfmask_preprocess'
generated using Kedro 0.19.10
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import apply_cfmask


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=apply_cfmask,
                inputs={
                    "dependency": "dependency2",
                    "dependency2": "dependency3",
                    "boa_path": "params:configs.boa_dowload_path",
                    "location_name": "params:configs.location_name",
                    "save_masks_path": "params:configs.save_masks_path",
                    "save_plots_path": "params:configs.save_plot_masks_path",
                    "scale_factor": "params:configs.scale_factor",
                    "skip_masks": "params:configs.skip_cfmasks",
                },
                outputs="dependency10",
                name="appy_CFMask",
            ),
        ]
    )
