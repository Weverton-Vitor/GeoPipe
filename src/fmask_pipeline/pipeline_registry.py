"""Project pipelines."""

import logging

import ee
from kedro.config import OmegaConfigLoader
from kedro.framework.project import find_pipelines
from kedro.pipeline import Pipeline, pipeline

from fmask_pipeline.pipelines.deepwatermap import pipeline as deepwatermap
from fmask_pipeline.pipelines.download_and_preprocess import (
    pipeline as download_and_preprocess,
)

logger = logging.getLogger(__name__)

ee.Authenticate()
ee.Initialize(project="ee-cloud-segmentation")

CONF_SOURCE = "conf/"
conf_loader = OmegaConfigLoader(CONF_SOURCE)
params = conf_loader["parameters"]


def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """

    water_volume_monitoring = pipeline(
        pipe=download_and_preprocess.create_pipeline() + deepwatermap.create_pipeline(),
        parameters=None,
    )

    return {
        "__default__": download_and_preprocess.create_pipeline(),
        "download_and_preprocess": download_and_preprocess.create_pipeline(),
        "water_volume_monitoring": water_volume_monitoring,
    }
