import logging
from pathlib import Path

import requests
import segmentation_models_pytorch as smp
import torch

logger = logging.getLogger(__name__)


def download_model(model_url: str, model_path: Path) -> None:
    """Realiza o download do modelo UNet a partir da URL fornecida."""
    logger.info("Fazendo download do modelo UNet...")
    response = requests.get(model_url, stream=True)
    response.raise_for_status()
    with open(model_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def load_unet_model(model_path: str = None):
    """
    Carrega o modelo UNet (MobileNet_v2) com 13 bandas de entrada e 4 classes de saída.
    Se o arquivo local não for encontrado, baixa automaticamente o modelo pré-treinado.
    """
    default_model_url = "https://huggingface.co/datasets/isp-uv-es/CloudSEN12Plus/resolve/main/demo/models/UNetMobV2_V2.pt"
    default_model_filename = "UNetMobV2_V2.pt"

    # Define o caminho do modelo utilizando Path
    if model_path is None:
        model_path = default_model_filename
    model_path = Path(model_path)

    # Se o arquivo não existir, realiza o download
    if not model_path.exists():
        download_model(default_model_url, model_path)

    # Cria a arquitetura da UNet
    model = smp.Unet(
        encoder_name="mobilenet_v2", encoder_weights=None, classes=4, in_channels=13
    )
    # Carrega os pesos do modelo
    state_dict = torch.load(str(model_path), map_location=torch.device("cpu"))
    model.load_state_dict(state_dict)

    # Desativa os gradientes e coloca o modelo em modo de avaliação
    for param in model.parameters():
        param.requires_grad = False
    model.eval()
    return model

