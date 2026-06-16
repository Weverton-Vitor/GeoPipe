"""
This is a boilerplate pipeline 'fmask_preprocess'
generated using Kedro 0.19.10
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import apply_fmask, cloud_removal, apply_cloud_mask


def create_pipeline(toa="TOA_download_images_dependency", boa="BOA_download_images_dependency", **kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=apply_cloud_mask,
                inputs={
                    "shapefile": "shapefile",
                    "mask_type": "params:configs.mask_type",
                    "dowload_path": "params:configs.masks_path",
                    "TOA_download_images_dependency": toa,
                    "BOA_download_images_dependency": boa,
                    "toa_path": "params:configs.toa_dowload_path",
                    "location_name": "params:configs.location_name",
                    "save_masks_path": "params:configs.save_masks_path",
                    "save_plots_path": "params:configs.save_plot_masks_path",
                    "scale": "params:configs.scale",
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
                    "path_images": "params:configs.boa_dowload_path",
                    "path_masks": "params:configs.save_masks_path",
                    "output_path": "params:configs.save_clean_images_path",
                    "algorithm": "params:configs.mask_type",                    
                    "location_name": "params:configs.location_name",
                    "cloud_and_cloud_shadow_pixels": "params:configs.cloud_and_cloud_shadow_pixels",
                    "init_date": "params:configs.init_date",
                    "final_date": "params:configs.final_date",
                    "skip_clean": "params:configs.skip_clean",
                    "color_file_log_path": "params:configs.cloud_removal_log",
                    "max_workers": "params:configs.max_workers_image_reconstruction",
                },
                outputs="cloud_removed_dependency",
                name="Cloud_removal",
            ),
        ]
    )
