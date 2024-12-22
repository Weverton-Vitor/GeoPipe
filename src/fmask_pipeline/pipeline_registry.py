"""Project pipelines."""

from kedro.framework.project import find_pipelines
from kedro.pipeline import Pipeline
from fmask_pipeline.pipelines import download_and_preprocess
import ee

ee.Authenticate()
ee.Initialize(project="ee-cloud-segmentation")

def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """
    pipelines = find_pipelines()
    pipelines["__default__"] = sum(pipelines.values())
    return {
        "__default__": download_and_preprocess.create_pipeline(),
        "download_and_preprocess": download_and_preprocess.create_pipeline(),
    }
