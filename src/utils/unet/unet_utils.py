import logging
from pathlib import Path
from typing import Optional

import requests
import segmentation_models_pytorch as smp
import torch

logger = logging.getLogger(__name__)

# Pesos do modelo original (UNet com encoder MobileNet_v2)
_MOBILENET_DEFAULT_URL = (
    "https://huggingface.co/datasets/isp-uv-es/CloudSEN12Plus/"
    "resolve/main/demo/models/UNetMobV2_V2.pt"
)
_MOBILENET_DEFAULT_FILENAME = "UNetMobV2_V2.pt"

# Pesos do novo modelo (UNet com encoder RegNetZ D8)
_REGNETZ_D8_DEFAULT_URL = (
    "https://huggingface.co/Burdenthrive/cloud-detection-unet-regnetzd8/"
    "resolve/main/unet_regnetz_d8.pth"
)
_REGNETZ_D8_DEFAULT_FILENAME = "unet_regnetz_d8.pth"


def download_model(model_url: str, model_path: Path, chunk_size: int = 8192) -> None:
    """
    Faz o download de um arquivo de pesos de modelo para o caminho indicado.

    Parameters
    ----------
    model_url : str
        URL do arquivo de pesos.
    model_path : Path
        Caminho de destino para salvar o arquivo.
    chunk_size : int
        Tamanho do chunk para streaming.
    """
    logger.info("Baixando pesos do modelo: %s", model_url)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(model_url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(model_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
    logger.info("Pesos salvos em: %s", model_path)


def _ensure_weights(path: Path, url: str) -> None:
    """
    Garante que o arquivo de pesos exista localmente; caso contrário, faz o download.
    """
    if not path.exists():
        logger.info("Arquivo de pesos não encontrado em '%s'. Será feito o download.", path)
        download_model(url, path)
    else:
        logger.info("Usando pesos locais: %s", path)


def _load_state_dict_with_possible_prefix(
    model: torch.nn.Module, state_dict: dict
) -> None:
    """
    Carrega o state_dict no modelo. Caso as chaves estejam prefixadas com 'unet.'
    (padrão comum quando a rede foi salva dentro de um wrapper), remove o prefixo
    e tenta novamente. Por fim, realiza um load não estrito se necessário.
    """
    try:
        model.load_state_dict(state_dict, strict=True)
        return
    except RuntimeError as e:
        # Tenta remover o prefixo 'unet.' (como no wrapper de HF).
        if any(k.startswith("unet.") for k in state_dict.keys()):
            stripped = {k.replace("unet.", "", 1): v for k, v in state_dict.items()}
            model.load_state_dict(stripped, strict=True)
            return
        logger.warning(
            "Falha no carregamento estrito dos pesos (%s). Tentando modo não estrito.", e
        )
        model.load_state_dict(state_dict, strict=False)


def load_unet_mobilenet_v2_model(model_path: Optional[str] = None) -> torch.nn.Module:
    """
    Carrega uma UNet (smp.Unet) com encoder MobileNet_v2,
    13 canais de entrada (Sentinel‑2) e 4 classes de saída.

    Parameters
    ----------
    model_path : Optional[str]
        Caminho para o arquivo de pesos. Se None, usa o padrão.

    Returns
    -------
    torch.nn.Module
        Modelo PyTorch pronto para inferência (eval e sem gradientes).
    """
    path = Path(model_path or _MOBILENET_DEFAULT_FILENAME)
    _ensure_weights(path, _MOBILENET_DEFAULT_URL)

    model = smp.Unet(
        encoder_name="mobilenet_v2",
        encoder_weights=None,
        classes=4,
        in_channels=13,
    )
    state = torch.load(str(path), map_location=torch.device("cpu"))
    _load_state_dict_with_possible_prefix(model, state)

    for p in model.parameters():
        p.requires_grad = False
    model.eval()
    return model


def load_unet_regnetz_d8_model(model_path: Optional[str] = None) -> torch.nn.Module:
    """
    Carrega uma UNet (smp.Unet) com encoder RegNetZ D8 (via TIMM),
    13 canais de entrada e 4 classes de saída.

    Parameters
    ----------
    model_path : Optional[str]
        Caminho para o arquivo de pesos. Se None, usa o padrão do HF.

    Returns
    -------
    torch.nn.Module
        Modelo PyTorch pronto para inferência (eval e sem gradientes).
    """
    path = Path(model_path or _REGNETZ_D8_DEFAULT_FILENAME)
    _ensure_weights(path, _REGNETZ_D8_DEFAULT_URL)

    # Importante: o nome do encoder no segmentation_models_pytorch
    # para os encoders do timm costuma usar o prefixo 'tu-'.
    model = smp.Unet(
        encoder_name="tu-regnetz_d8",
        encoder_weights=None,
        classes=4,
        in_channels=13,
    )
    state = torch.load(str(path), map_location=torch.device("cpu"))
    _load_state_dict_with_possible_prefix(model, state)

    for p in model.parameters():
        p.requires_grad = False
    model.eval()
    return model


def load_unet_model(
    model_path: Optional[str] = None,
    architecture: Optional[str] = None,
) -> torch.nn.Module:
    """
    Loader *backward-compatible* usado em toda a pipeline.

    - Se `architecture` for informado, escolhe explicitamente o backbone.
    - Caso contrário, tenta inferir a partir do nome do arquivo de pesos.
    - Em último caso, usa o modelo padrão (MobileNet_v2).

    Isso permite trocar apenas o `model_weights` no parameters.yml (por exemplo,
    para "unet_regnetz_d8.pth") sem alterar o restante do código ou da pipeline.

    Parameters
    ----------
    model_path : Optional[str]
        Caminho para o arquivo de pesos (ou None para padrão).
    architecture : Optional[str]
        Nome do backbone. Exemplos: "mobilenet_v2", "regnetz_d8" (ou "tu-regnetz_d8").

    Returns
    -------
    torch.nn.Module
        Modelo PyTorch pronto para inferência.
    """
    arch = (architecture or "").lower()

    # Escolha explícita por parâmetro
    if arch in {"regnetz_d8", "tu-regnetz_d8", "regnetz", "regnetzd8"}:
        return load_unet_regnetz_d8_model(model_path)
    if arch in {"mobilenet_v2", "mobilenet"}:
        return load_unet_mobilenet_v2_model(model_path)

    # Inferência automática pelo nome do arquivo
    if model_path:
        name = Path(model_path).name.lower()
        if "regnetz" in name or "regnet" in name or name.endswith("d8.pth"):
            return load_unet_regnetz_d8_model(model_path)

    # Fallback: modelo padrão (MobileNet_v2)
    return load_unet_mobilenet_v2_model(model_path)
