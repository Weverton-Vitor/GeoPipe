"""
This is a boilerplate pipeline 'fmask_preprocess'
generated using Kedro 0.19.10
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import apply_cloud_mask, cloud_removal


def create_pipeline(
    toa="TOA_download_images_dependency", boa="BOA_download_images_dependency", **kwargs
) -> Pipeline:
    return pipeline(
        [
            node(
                func=apply_cloud_mask,
                inputs={
                    "shapefile": "shapefile",
                    "mask_type": "params:configs.cloud_mask_algoritm",
                    "dowload_path": "params:paths.cloud_masks_save_path",
                    "TOA_download_images_dependency": toa,
                    "BOA_download_images_dependency": boa,
                    "toa_path": "params:paths.toa_dowload_save_path",
                    "location_name": "params:configs.location_name",
                    "save_masks_path": "params:paths.cloud_masks_save_path",
                    "save_plots_path": "params:paths.plot_masks_save_path",
                    "scale": "params:configs.scale_factor",
                    "skip_masks": "params:configs.skip_masks",
                    "init_date": "params:configs.init_date",
                    "final_date": "params:configs.final_date",
                    "prefix_images_name": "params:configs.toa_prefix_images_name",
                },
                outputs="Fmask_dependency",
                name="apply_cloud_masks",
            ),
            node(
                func=cloud_removal,
                inputs={
                    "dependency": "Fmask_dependency",
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
