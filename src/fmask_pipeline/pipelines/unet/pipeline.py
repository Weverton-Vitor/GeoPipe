"""
This is a boilerplate pipeline 'unet'
generated using Kedro 0.19.12
"""

from kedro.pipeline import Pipeline, node, pipeline

from fmask_pipeline.pipelines.cloud_preprocess.nodes import cloud_removal  # noqa

from .nodes import apply_unet


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=apply_unet,
                inputs={
                    "TOA_download_images_dependency": "TOA_download_images_dependency",
                    "BOA_download_images_dependency": "BOA_download_images_dependency",
                    "toa_path": "params:paths.toa_dowload_save_path",
                    "location_name": "params:configs.location_name",
                    "save_masks_path": "params:paths.cloud_masks_save_path",
                    "save_plots_path": "params:paths.plot_masks_save_path",
                    "skip_masks": "params:configs.skip_unet_masks",
                    "unet_params": "params:configs.unet",
                    "scale_factor": "params:configs.scale_factor",
                },
                outputs="unet_segmentation_output",
                name="apply_UNet",
            ),
            node(
                func=cloud_removal,
                inputs={
                    "dependency": "unet_segmentation_output",
                    "path_images": "params:paths.boa_dowload_path_save_path",
                    "path_masks": "params:paths.cloud_masks_save_path",
                    "output_path": "params:paths.clean_images_save_path",
                    "location_name": "params:configs.location_name",
                    "cloud_and_cloud_shadow_pixels": "params:configs.cloud_and_cloud_shadow_pixels",
                    "init_date": "params:configs.init_date",
                    "final_date": "params:configs.final_date",
                    "skip_clean": "params:configs.skip_clean",
                    "color_file_log_path": "params:paths.cloud_removal_log_save_path",
                },
                outputs="cloud_removed_dependency",
                name="Cloud_removal",
            ),
        ]
    )