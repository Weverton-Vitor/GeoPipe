from pathlib import Path

from kedro.config import OmegaConfigLoader

conf_path = Path("base")
conf_loader = OmegaConfigLoader(conf_source=conf_path)

parameters = conf_loader.get("parameters*")

print(f"parameters: {parameters}")
print(f"parameters: {parameters}")
print(f"parameters: {parameters}")
print(f"parameters: {parameters}")
print(f"parameters: {parameters}")

WATER_SEGMENTATION_MODELS = {
    "VGG-UNet": f"{parameters['water_model_name']}/vgg-unet.onnx",
    "WatNet": f"{parameters['water_model_name']}/watnet.onnx",
    "DeepWaterMap": f"{parameters['water_model_name']}/deepwatermap.onnx",
    "NDWI": "NDWI",
    "MNDWI": "MNDWI",
}