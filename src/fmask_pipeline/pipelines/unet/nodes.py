import glob
import logging
import os
from pathlib import Path

import numpy as np
import rasterio
import torch
from tqdm import tqdm

from utils.cloud_removal.bcl import BCL
from utils.pytorch.pytorch_general_utils import torch_model_cloud_and_shadows_inference
from utils.unet.unet_utils import load_unet_model

logger = logging.getLogger(__name__)

def apply_unet(
    toa_path: str,
    location_name: str,
    save_masks_path: str,
    save_plots_path: str,
    skip_masks: bool = False,
    model_path: str = None,
    unet_params: dict = None,
    *args,
    **kwargs,
):
    """
    Aplica a UNet para inferir máscaras de nuvem e sombra, combina com a máscara de água
    (se existir) e salva o resultado como um único TIF e um PNG de visualização.

    Args:
        toa_path (str): Caminho base das imagens (TOA).
        location_name (str): Nome do local/pasta.
        save_masks_path (str): Caminho para salvar as máscaras TIF combinadas.
        save_plots_path (str): Caminho para salvar os plots PNG combinados.
        skip_masks (bool, opcional): Se True, pula a geração das máscaras. Default é False.
        model_path (str, opcional): Caminho do modelo UNet. Default é None.
        unet_params (dict, opcional): Parâmetros adicionais para a UNet. Default é None.
    """
    if skip_masks:
        logger.warning("Pular geração das máscaras com UNet")
        return True

    unet_params = unet_params or {}
    model_weights = unet_params.get("model_weights", None)
    cloud_thick_class = unet_params.get("cloud_thick_class", 1)
    cloud_thin_class = unet_params.get("cloud_thin_class", 2)
    cloud_shadow_class = unet_params.get("cloud_shadow_class", 3)

    # Carrega o modelo (priorizando o caminho definido em unet_params)
    model = load_unet_model(model_weights if model_weights else model_path)

    # Procura os arquivos TIFF com 13 bandas usando pathlib
    inputs = list(Path(toa_path, location_name).rglob("*.tif"))
    total_tifs = len(inputs)


    with tqdm(
        total=total_tifs, desc="Segmenting Clouds and Cloud Shadows - UNet", unit="images"
    ) as pbar:
        for inp in inputs:
            # Define o nome do arquivo de saída com base na estrutura de diretórios
            file_parts = inp.parts[-2:]
            file_name = f"{location_name}/{file_parts[0]}/unet_mask_{inp.stem}"
            torch_model_cloud_and_shadows_inference(
                input_tif_path=inp,
                location_name=location_name,
                save_masks_path=save_masks_path,
                save_plots_path=save_plots_path,
                file_name=file_name,
                cloud_classes=[cloud_thick_class, cloud_thin_class],
                cloud_shadows_classes=cloud_shadow_class,
                model=model,
            )
            pbar.update(1)

    return True
