import os

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.patches import Patch
from segmentation_mask_overlay import overlay_masks
from PIL import Image, ImageDraw


def calculate_ndvi(red: np.ndarray, nir: np.ndarray) -> tuple[np.ndarray]:
    """Calculate the NDVI spectral indice by: nir-red/nir+red

    Red band -> landsat4-5 TM: B3
                  landsat7 ETM: B3
                  Sentinel 2: B4

    NIR band -> landsat4-5 TM: B4
                landsat7 ETM: B4
                Sentinel 2: B8

    Args:
        red (np.ndarray): Red band
        nir (np.ndarray): Nir band

    Returns:
        List[np.ndarray]: A single band with the np.ndarray
    """

    ndvi = (nir - red) / (nir + red)

    modified_ndvi = ndvi.copy()

    b3_0_to_255 = np.max((nir - np.min(nir)) / (np.max(nir) - np.min(nir)) * 255)

    pixels_to_modify = (b3_0_to_255 == 255) & (red > nir)

    modified_ndvi[pixels_to_modify] = 0

    # plt.figure()
    # plt.imshow(ndvi, cmap='Greens')
    # plt.show()

    return ndvi, modified_ndvi


def calculate_ndsi(green: np.ndarray, swir1: np.ndarray) -> tuple[np.ndarray]:
    """_summary_

    Green band -> landsat4-5 TM: B2
                  landsat7 ETM: B2
                  Sentinel 2: B3

    SWIR band -> landsat4-5 TM: B5
                landsat7 ETM: B5
                Sentinel 2: B11

    Args:
        green (np.ndarray): Green band
        swir1 (np.ndarray): Shortwave Infrared 1 band

    Returns:
        tuple: common ndsi and modified ndsi
    """

    ndsi = (green - swir1) / (green + swir1)

    modified_ndsi = ndsi.copy()

    b2_0_to_255 = np.max(
        (green - np.min(green)) / (np.max(green) - np.min(green)) * 255
    )

    # Saturation test
    pixels_to_modify = (b2_0_to_255 == 255) & (swir1 > green)

    modified_ndsi[pixels_to_modify] = 0

    return ndsi, modified_ndsi


def calculate_ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Calculate the NDVI spectral indice by: nir-red/nir+red

    Green band -> landsat4-5 TM: B2
                  landsat7 ETM: B2
                  Sentinel 2: B3

    NIR band -> landsat4-5 TM: B4
                landsat7 ETM: B4
                Sentinel 2: B8


    Args:
        green (np.ndarray): Green band
        nir (np.ndarray): NIR band

    Returns:
        np.ndarray: A single band with the np.ndarray
    """

    ndwi = (green - nir) / (green + nir)

    return ndwi


def calculate_brightness_temperature(band_thermal, k1, k2, to_celsius=False):
    radiance = band_thermal * 0.05518 + 1.2378
    bt_kelvin = k2 / np.log((k1 / radiance) + 1)
    if to_celsius:
        bt_celsius = bt_kelvin - 273.15
        return bt_celsius
    else:
        return bt_kelvin


def calculate_flood_fill_transformation(band: np.ndarray):
    # Normalizar a banda para o intervalo [0, 255]
    band4_normalized = (
        (band - np.min(band)) / (np.max(band) - np.min(band)) * 255
    ).astype(np.uint8)
    normalized_image = Image.fromarray(band4_normalized)

    # Inverter a imagem para que o flood-fill funcione corretamente (transformação morfológica)
    inverted_image = Image.fromarray(255 - band4_normalized)

    # Definir um ponto de partida fora da área de interesse (por exemplo, canto da imagem)
    seed_point = (0, 0)

    # Aplicar o flood-fill usando ImageDraw.floodfill
    ImageDraw.floodfill(inverted_image, xy=seed_point, value=255, thresh=00)

    # Inverter a imagem de volta ao original
    filled_image = Image.fromarray(255 - np.array(inverted_image))

    # Converter o resultado de volta para um array NumPy
    result = np.maximum(band4_normalized, np.array(filled_image))

    # Converter o resultado de volta para uma imagem PIL
    result_image = Image.fromarray(result.astype(np.uint8) // 255)

    return result_image


def save_one_band_tif(self, band: np.ndarray, tif_file: str, output_file: str) -> None:
    """_summary_

    Args:
        band (np.ndarray): _description_
        tif_file (str): _description_
        output_file (str): _description_
    """

    with rasterio.open(tif_file) as src:
        profile = src.profile
        profile.update(count=1)
        with rasterio.open(output_file, "w", **profile) as dst:
            dst.write(band, 1)


def save_overlayed_mask_plot(
    masks: list, color_composite: np.ndarray, output_file: str
) -> None:
    """Save a plot contains mask with mask

    Args:
        mask (np.ndarray): Final mask
        color_composite (str): A color composite with three bands
        save_dir (str): Directory to save the plot
    """

    fig = plt.figure(figsize=(25, 15))
    plt.subplot(1, 2, 1)
    color_composite = (color_composite - color_composite.min()) / (
        color_composite.max() - color_composite.min()
    )
    plt.imshow(color_composite, interpolation="nearest", aspect="auto")
    plt.axis(False)

    colors = ["gold", "red", "blue"]
    classes = ["Nuvem", "Sombra de Nuvem", "Água"]
    masked_image = overlay_masks(
        color_composite, np.stack(masks, -1), classes, colors=colors
    )

    plt.subplot(1, 2, 2)
    plt.imshow(color_composite, interpolation="nearest", aspect="auto")
    plt.imshow(masked_image, alpha=1, interpolation="nearest", aspect="auto")

    legend_elements = [
        Patch(facecolor=colors[i], edgecolor="black", label=f"{classes[i]}")
        for i in range(len(colors))
    ]

    plt.legend(handles=legend_elements, loc="upper right", fontsize=25)
    plt.axis(False)

    os.makedirs("/".join(output_file.split("/")[:-1]), exist_ok=True)

    fig.savefig(output_file, dpi=fig.dpi)


def save_mask_tif(
    cloud_mask: np.ndarray,
    cloud_shadow_mask: np.ndarray,
    water_mask: np.ndarray,
    original_tif_file: str,
    output_file: str,
) -> None:
    """_summary_

    Args:
        band (np.ndarray): _description_
        tif_file (str): _description_
        output_file (str): _description_
    """

    mask_final = np.zeros_like(cloud_mask).astype(np.int8)

    mask_final[water_mask] = 3
    mask_final[cloud_shadow_mask] = 2
    mask_final[cloud_mask] = 1

    os.makedirs("/".join(output_file.split("/")[:-1]), exist_ok=True)

    with rasterio.open(original_tif_file) as src:
        profile = src.profile
        profile.update(count=1)
        with rasterio.open(output_file, "w", **profile) as dst:
            dst.write(mask_final, 1)


def read_bands(tif_file: str) -> np.ndarray:
    """Read all bands of a tif file

    Args:
        tif_file (str): A string with the path to the tif

    Returns:
        np.ndarray: ndarray with all tif band
    """
    with rasterio.open(tif_file) as src:
        bands = src.read()

    return bands
