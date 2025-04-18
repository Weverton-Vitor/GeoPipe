"""Project pipelines."""

import logging

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

logger = logging.getLogger(__name__)

CONF_SOURCE = "conf/"
conf_loader = OmegaConfigLoader(CONF_SOURCE)
params = conf_loader["parameters"]

# ee.Authenticate()
# ee.Initialize(project=params["configs"]["ee_project"])
# ee.Initialize()

import json
import ee

key_path = "/home/kedro_docker/key.json"
# Carregar o arquivo key.json
with open(key_path, "r") as f:
    key_data = json.load(f)

# Pegar o email da conta de serviço
service_account = key_data["client_email"]

# Inicializar Earth Engine com as credenciais
credentials = ee.ServiceAccountCredentials(
    service_account, key_path
)
ee.Initialize(credentials)

logger.info(f"Autenticado com a conta de serviço: {service_account}")


def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """

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
    }
