from pathlib import Path

from kedro.config import OmegaConfigLoader

conf_path = Path("../../../base")
conf_loader = OmegaConfigLoader(
    conf_source=conf_path, config_patterns={"parameters": ["parameters*"]}
)

parameters = conf_loader.get("parameters*")


WATER_SEGMENTATION_MODELS = {
    "vgg-unet": {
        "model_path": f"data/00_models/vgg-unet.onnx",
        "thresholds": [0.005, 0.01, 0.05, 0.1, 0.15, 0.25, 0.5, 0.75, 0.8, 0.95, 0.99],
    },
    "watnet": {
        "model_path": f"data/00_models/watnet.onnx",
        "thresholds": [0.005, 0.01, 0.05, 0.1, 0.15, 0.25, 0.5, 0.75, 0.8, 0.95, 0.99],
    },
    "deepwatermap": {
        "model_path": f"data/00_models/deepwatermap.onnx",
        "thresholds": [0.005, 0.01, 0.05, 0.1, 0.15, 0.25, 0.5, 0.75, 0.8, 0.95, 0.99],
    },
    "ndwi": {
        "model_path": "NDWI",
        "thresholds": [-0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
    },
    "mndwi": {
        "model_path": "MNDWI",
        "thresholds": [-0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
    },
}
