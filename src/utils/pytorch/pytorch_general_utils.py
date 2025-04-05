import logging
from pathlib import Path

import numpy as np
import torch
from rasterio import open as rio_open

from utils.fmask.fmask_utils import save_mask_tif, save_overlayed_mask_plot

logger = logging.getLogger(__name__)


# TODO : Turns this into a class and generalize to landsat series
def torch_model_cloud_and_shadows_inference(
    input_tif_path: Path,
    model,
    save_mask_path: str,
    save_plot_path: str,
    save_file_name: str,
    scale_factor: float,
    cloud_classes: list=[],
    cloud_shadows_classes: list=[],
    water_masks_classes: list=[],
):
    # Abre a imagem e normaliza os valores
    try:
        with rio_open(str(input_tif_path)) as src:
            image_array = src.read()  # (bands, height, width)
            image_array = image_array * scale_factor
    except Exception as e:
        logger.error(f"Erro ao abrir a imagem {input_tif_path}: {e}")

    if image_array.shape[0] != 13:
        logger.error(
            f"Imagem {input_tif_path} não possui 13 canais. Verifique os dados de entrada."
        )

    # Converte a imagem para tensor e realiza a inferência
    input_tensor = torch.from_numpy(image_array).unsqueeze(0).float()
    with torch.no_grad():
        output = model(input_tensor)
        segmentation_mask = output.argmax(dim=1).numpy().squeeze()

    # Cria máscaras separadas para nuvem e sombra
    cloud_mask = np.zeros_like(segmentation_mask, dtype=np.uint8)
    cloud_mask[np.isin(segmentation_mask, cloud_classes)] = 1

    cloud_shadow_mask = np.zeros_like(segmentation_mask, dtype=np.uint8)
    cloud_shadow_mask[segmentation_mask == cloud_shadows_classes] = 2

    water_mask = np.zeros_like(segmentation_mask, dtype=np.uint8)
    if water_masks_classes:
        water_mask[segmentation_mask == water_masks_classes] = 3

    # Gera uma composição colorida para o plot utilizando as bandas 4, 3 e 2 (índices 3, 2, 1)
    color_composite = image_array[[3, 2, 1], :, :]
    color_composite = np.transpose(color_composite, (1, 2, 0))  # (H, W, 3)

    # Garante que os diretórios de saída existam
    output_png = Path(save_plot_path, f"{save_file_name}.png")
    output_png.parent.mkdir(parents=True, exist_ok=True)

    output_tif = Path(save_mask_path, f"{save_file_name}.tif")
    output_tif.parent.mkdir(parents=True, exist_ok=True)

    # Salva o plot com as máscaras sobrepostas
    save_overlayed_mask_plot(
        masks=[cloud_mask, cloud_shadow_mask, water_mask],
        color_composite=color_composite,
        output_file=str(output_png),
    )

    # Salva o TIF com as 3 classes (1=nuvem, 2=sombra, 3=água)
    save_mask_tif(
        cloud_mask=cloud_mask,
        cloud_shadow_mask=cloud_shadow_mask,
        water_mask=water_mask,
        original_tif_file=str(input_tif_path),
        output_file=str(output_tif),
    )
