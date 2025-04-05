"""
This is a boilerplate pipeline 'fmask_preprocess'
generated using Kedro 0.19.10
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import apply_fmask, cloud_removal


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=apply_fmask,
                inputs={
                    "TOA_download_images_dependency": "TOA_download_images_dependency",
                    "BOA_download_images_dependency": "BOA_download_images_dependency",
                    "toa_path": "params:configs.toa_dowload_path",
                    "location_name": "params:configs.location_name",
                    "save_masks_path": "params:configs.save_masks_path",
                    "save_plots_path": "params:configs.save_plot_masks_path",
                    "scale_factor": "params:configs.scale_factor",
                    "skip_masks": "params:configs.skip_masks",
                },
                outputs="Fmask_dependency",
                name="appy_FMask",
            ),
            node(
                func=cloud_removal,
                inputs={
                    "dependency": "Fmask_dependency",
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
