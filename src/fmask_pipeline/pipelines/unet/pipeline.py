"""
This is a boilerplate pipeline 'unet'
generated using Kedro 0.19.12
"""

from kedro.pipeline import Pipeline, node, pipeline

from fmask_pipeline.pipelines.fmask_preprocess.nodes import cloud_removal  # noqa

from .nodes import apply_unet


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=apply_unet,
                inputs={
                    "TOA_download_images_dependency": "TOA_download_images_dependency",
                    "BOA_download_images_dependency": "BOA_download_images_dependency",
                    "toa_path": "params:configs.toa_dowload_path",
                    "location_name": "params:configs.location_name",
                    "save_masks_path": "params:configs.save_masks_path",
                    "save_plots_path": "params:configs.save_plot_masks_path",
                    "skip_masks": "params:configs.skip_unet_masks",
                    "unet_params": "params:configs.unet",
                },
                outputs="unet_segmentation_output",
                name="apply_UNet",
            ),
            node(
                func=cloud_removal,
                inputs={
                    "dependency": "unet_segmentation_output",
                    "path_images": "params:configs.boa_dowload_path",
                    "path_masks": "params:configs.save_masks_path",
                    "output_path": "params:configs.save_clean_images_path",
                    "location_name": "params:configs.location_name",
                    "cloud_and_cloud_shadow_pixels": "params:configs.cloud_and_cloud_shadow_pixels",
                    "init_date": "params:configs.init_date",
                    "final_date": "params:configs.final_date",
                    "skip_clean": "params:configs.skip_clean",
                    "color_file_log_path": "params:configs.cloud_removal_log",
                },
                outputs="cloud_removed_dependency",
                name="Cloud_removal",
            ),
        ]
    )