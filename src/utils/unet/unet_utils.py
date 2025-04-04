import os
import gc
import numpy as np
import rasterio
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

def save_mask_tif(binary_mask: np.ndarray, original_tif_file: str, output_file: str) -> None:
    """
    Salva a máscara binária em um arquivo TIFF usando o perfil do arquivo original.

    Args:
        binary_mask (np.ndarray): Máscara binária (valores 0 ou 1).
        original_tif_file (str): Caminho do TIFF original.
        output_file (str): Caminho de saída para salvar a máscara.
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with rasterio.open(original_tif_file) as src:
        profile = src.profile
        profile.update(count=1, dtype="uint8")
        with rasterio.open(output_file, "w", **profile) as dst:
            dst.write(binary_mask.astype("uint8"), 1)
    gc.collect()


def save_overlayed_mask_plot(binary_mask: np.ndarray, color_composite: np.ndarray, output_file: str) -> None:
    """
    Salva uma figura com a imagem original e a máscara binária sobreposta.

    Args:
        binary_mask (np.ndarray): Máscara binária (valores 0 ou 1).
        color_composite (np.ndarray): Imagem original (por exemplo, composição RGB ou normalizada).
        output_file (str): Caminho para salvar a figura.
    """
    # Normaliza a imagem original para visualização
    norm_img = (color_composite - np.min(color_composite)) / (np.ptp(color_composite))
    
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(norm_img, interpolation="nearest")
    
    # Sobrepõe a máscara em vermelho onde binary_mask == 1
    # Usamos uma máscara para esconder os valores 0
    masked = np.ma.masked_where(binary_mask == 0, binary_mask)
    ax.imshow(masked, cmap="Reds", alpha=0.5, interpolation="nearest")
    
    ax.axis("off")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    fig.savefig(output_file, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    gc.collect()
