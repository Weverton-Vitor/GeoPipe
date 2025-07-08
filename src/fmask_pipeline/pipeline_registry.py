"""Project pipelines."""

import logging
from pathlib import Path

import ee
from kedro.config import OmegaConfigLoader
from kedro.framework.project import find_pipelines
from kedro.pipeline import Pipeline, pipeline

from fmask_pipeline.pipelines.canny import pipeline as canny
from fmask_pipeline.pipelines.cfmask_preprocess import pipeline as cfmask_preprocess
from fmask_pipeline.pipelines.deepwatermap import pipeline as deepwatermap
from fmask_pipeline.pipelines.download import (
    pipeline as download,
)
from fmask_pipeline.pipelines.fmask_preprocess import pipeline as fmask_preprocess
from fmask_pipeline.pipelines.unet import pipeline as unet
from fmask_pipeline.pipelines.calculate_spectral_indices import pipeline as calculate_spectral_indices
from utils.gee.authenticate import authenticate_earth_engine

logger = logging.getLogger(__name__)

CONF_SOURCE = "conf/"
conf_loader = OmegaConfigLoader(CONF_SOURCE)
params = conf_loader["parameters"]

# key_path = Path("/home/kedro_docker/key.json")
key_path = Path("C:/Users/weverton.vitor/Documents/faculdade/pibic/fmask-pipeline/key.json")
authenticate_earth_engine(key_path)

def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """

    water_area_monitoring_sentinel_spectral_indice = pipeline(
        pipe=download.create_pipeline()
        + calculate_spectral_indices.create_pipeline(dependencies=["created_spectral_indice_dirs_dependency", "BOA_download_images_dependency"]),
        parameters=None,
    )

    water_area_monitoring_sentinel_fmask_spectral_indice = pipeline(
        pipe=download.create_pipeline()
        + fmask_preprocess.create_pipeline()
        + calculate_spectral_indices.create_pipeline(["created_spectral_indice_dirs_dependency", "BOA_download_images_dependency", "cloud_removed_dependency"]),
        parameters=None,
    )

    water_area_monitoring_sentinel_deepwatermap = pipeline(
        pipe=download.create_pipeline()
        + deepwatermap.create_pipeline(["created_deep_water_map_dirs_dependency", "BOA_download_images_dependency"]),
        parameters=None,
    )

    water_volume_monitoring_sentinel_fmask_deepwatermap = pipeline(
        pipe=download.create_pipeline()
        + fmask_preprocess.create_pipeline()
        + deepwatermap.create_pipeline(),
        parameters=None,
    )

    water_volume_monitoring_sentinel_unet_deepwatermap = pipeline(
        pipe=download.create_pipeline()
        + unet.create_pipeline()
        + deepwatermap.create_pipeline(),
        parameters=None,
    )

    coastline_fmask_sentinel_deepwatermap = pipeline(
        pipe=download.create_pipeline()
        + fmask_preprocess.create_pipeline()
        + deepwatermap.create_pipeline()
        + canny.create_pipeline(),
        parameters=None,
    )

    coastline_cfmask_landsat_deepwatermap = pipeline(
        pipe=download.create_pipeline()
        + cfmask_preprocess.create_pipeline()
        + deepwatermap.create_pipeline()
        + canny.create_pipeline(),
        parameters=None,
    )


    return {
        "__default__": download.create_pipeline(),
        "download": download.create_pipeline(),
        "fmask_preprocessing": fmask_preprocess.create_pipeline(),
        "apply_deepwatermap": deepwatermap.create_pipeline(),
        "apply_canny": canny.create_pipeline(),
        "water_volume_monitoring_sentinel_fmask_deepwatermap": water_volume_monitoring_sentinel_fmask_deepwatermap,
        "water_volume_monitoring_sentinel_unet_deepwatermap": water_volume_monitoring_sentinel_unet_deepwatermap,
        "coastline_fmask_sentinel_deepwatermap": coastline_fmask_sentinel_deepwatermap,
        "coastline_cfmask_landsat_deepwatermap": coastline_cfmask_landsat_deepwatermap,
        "water_area_monitoring_sentinel_deepwatermap": water_area_monitoring_sentinel_deepwatermap,
        "water_area_monitoring_sentinel_spectral_indice": water_area_monitoring_sentinel_spectral_indice,
        "water_area_monitoring_sentinel_fmask_spectral_indice": water_area_monitoring_sentinel_fmask_spectral_indice
    }
    
