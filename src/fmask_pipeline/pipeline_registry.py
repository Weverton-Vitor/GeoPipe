"""Project pipelines."""

import logging

import ee
from kedro.config import OmegaConfigLoader
from kedro.framework.project import find_pipelines
from kedro.pipeline import Pipeline, pipeline

from fmask_pipeline.pipelines.deepwatermap import pipeline as deepwatermap
from fmask_pipeline.pipelines.download import (
    pipeline as download,
)
from fmask_pipeline.pipelines.fmask_preprocess import pipeline as fmask_preprocess

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

    water_volume_monitoring_fmask = pipeline(
        pipe=download.create_pipeline()
        + fmask_preprocess.create_pipeline()
        + deepwatermap.create_pipeline(),
        parameters=None,
    )

    return {
        "__default__": download.create_pipeline(),
        "download": download.create_pipeline(),
        "fmask_preprocessing": fmask_preprocess.create_pipeline(),
        "apply_deepwatermap": deepwatermap.create_pipeline(),
        "water_volume_monitoring_fmask": water_volume_monitoring_fmask,
    }
