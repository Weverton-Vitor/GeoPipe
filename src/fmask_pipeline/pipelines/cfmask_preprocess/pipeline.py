"""
This is a boilerplate pipeline 'cfmask_preprocess'
generated using Kedro 0.19.10
"""

from kedro.pipeline import Pipeline, node, pipeline

from fmask_pipeline.pipelines.cloud_preprocess.nodes import cloud_removal

from .nodes import apply_cfmask


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=apply_cfmask,
                inputs={
                    "dependency": "TOA_download_images_dependency",
                    "TOA_download_images_dependency": "BOA_download_images_dependency",
                    "boa_path": "params:paths.boa_dowload_path_save_path",
                    "location_name": "params:configs.location_name",
                    "save_masks_path": "params:paths.cloud_masks_save_path",
                    "save_plots_path": "params:paths.plot_masks_save_path",
                    "scale_factor": "params:configs.scale_factor",
                    "skip_masks": "params:configs.skip_cfmasks",
                },
                outputs="CF_mask_dependency",
                name="apply_CFMask",
            ),
            node(
                func=cloud_removal,
                inputs={
                    "dependency": "CF_mask_dependency",
                    "path_images": "params:paths.boa_dowload_path_save_path",
                    "path_masks": "params:paths.cloud_masks_save_path",
                    "output_path": "params:paths.clean_images_save_path",
                    "location_name": "params:configs.location_name",
                    "cloud_and_cloud_shadow_pixels": "params:configs.cloud_and_cloud_shadow_pixels",
                    "init_date": "params:configs.init_date",
                    "final_date": "params:configs.final_date",
                    "skip_clean": "params:configs.skip_clean",
                    "color_file_log_path": "params:paths.cloud_removal_log_save_path",
                    "cloud_mask_algorithm": "params:configs.cloud_mask_algoritm",
                    "reconstruction_algorithm": "params:configs.reconstruction_algorithm",
                    "max_workers": "params:configs.max_workers_image_reconstruction",
                },
                outputs="cloud_removed_dependency",
                name="Cloud_removal",
            ),
        ]
    )
