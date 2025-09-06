import logging
from pathlib import Path
from typing import Any, Dict, Optional

from tqdm import tqdm

from utils.pytorch.pytorch_general_utils import (
    torch_model_cloud_and_shadows_inference,
)
from utils.unet.unet_utils import load_unet_model

logger = logging.getLogger(__name__)


def apply_unet(
    toa_path: str,
    location_name: str,
    save_masks_path: str,
    save_plots_path: str,
    skip_masks: bool = False,
    model_path: Optional[str] = None,
    unet_params: Optional[Dict[str, Any]] = None,
    scale_factor: float = 1.0,
    *args,
    **kwargs,
) -> bool:
    """
    Aplica a UNet para inferir máscaras de nuvem e sombra, combina com a
    máscara de água (se existir) e salva o resultado como um único TIF e um
    PNG de visualização.

    Parâmetros
    ----------
    toa_path : str
        Caminho base onde estão as imagens TOA (organizadas por `location_name`).
    location_name : str
        Nome da localidade/pasta das imagens.
    save_masks_path : str
        Caminho onde serão salvos os TIFs de máscara.
    save_plots_path : str
        Caminho onde serão salvos os PNGs de visualização das máscaras.
    skip_masks : bool
        Se True, pula a geração das máscaras.
    model_path : Optional[str]
        Caminho explícito para os pesos do modelo (opcional).
    unet_params : Optional[Dict[str, Any]]
        Dicionário com parâmetros do UNet. Chaves suportadas:
        - "model_weights": caminho dos pesos (opcional; tem precedência sobre `model_path`)
        - "architecture": "mobilenet_v2" | "regnetz_d8" (opcional)
        - "cloud_thick_class": int (default=1)
        - "cloud_thin_class": int (default=2)
        - "cloud_shadow_class": int (default=3)
    scale_factor : float
        Fator multiplicativo aplicado nos valores de reflectância antes da inferência.

    Retorno
    -------
    bool
        True quando finaliza (ou quando `skip_masks=True`).
    """
    if skip_masks:
        logger.warning("Pular geração das máscaras com UNet")
        return True

    params = unet_params or {}

    # Lê parâmetros do modelo / classes
    model_weights = params.get("model_weights", model_path)
    architecture = params.get("architecture", None)  # e.g. "regnetz_d8" | "mobilenet_v2"
    cloud_thick_class = params.get("cloud_thick_class", 1)
    cloud_thin_class = params.get("cloud_thin_class", 2)
    cloud_shadow_class = params.get("cloud_shadow_class", 3)

    # Carrega o modelo respeitando a arquitetura solicitada (backward-compatible)
    model = load_unet_model(model_path=model_weights, architecture=architecture)

    # Procura os arquivos TIFF com 13 bandas
    inputs = list(Path(toa_path, location_name).rglob("*.tif"))
    total_tifs = len(inputs)

    if total_tifs == 0:
        logger.warning(
            "Nenhum arquivo .tif encontrado em '%s/%s' para segmentação UNet.",
            toa_path,
            location_name,
        )
        return True

    with tqdm(
        total=total_tifs,
        desc="Segmenting Clouds and Cloud Shadows - UNet",
        unit="images",
    ) as pbar:
        for inp in inputs:
            # Define o nome do arquivo de saída respeitando a estrutura atual
            file_parts = inp.parts[-2:]
            file_name = f"{location_name}/{file_parts[0]}/unet_mask_{inp.stem}"

            # Inferência e salvamento das saídas
            torch_model_cloud_and_shadows_inference(
                input_tif_path=inp,
                save_mask_path=save_masks_path,
                save_plot_path=save_plots_path,
                save_file_name=file_name,
                cloud_classes=[cloud_thick_class, cloud_thin_class],
                cloud_shadows_classes=[cloud_shadow_class],  # lista para np.isin
                model=model,
                scale_factor=scale_factor,
            )
            pbar.update(1)

    return True
