import logging
import os

import cv2
import matplotlib.pyplot as plt
import numpy as np
import rasterio

logger = logging.getLogger(__name__)

class Canny:

    sigma: int = 1
    lower_factor: int = 3
    upper_factor: int = 9

    def __init__(self, sigma=1, lower_factor=3, upper_factor=9):
        self.sigma = sigma
        self.lower_factor = lower_factor
        self.upper_factor = upper_factor

    def detect_border(self, tif_path, output_path):
        img = cv2.imread(tif_path, cv2.IMREAD_UNCHANGED)

        if img is not None:
            # Converta para 32 bits
            img_32bit = img.astype(np.float32)

            # Converta para 8 bits usando cv2.normalize
            img_8bit = cv2.normalize(img_32bit, None, 0, 255, cv2.NORM_MINMAX).astype(
                np.uint8
            )

            # Autocanny
            median = np.median(img_8bit)

            # apply automatic Canny edge detection using the computed median
            lower = int(max(0, (self.lower_factor - self.sigma) * median))
            upper = int(min(255, (self.upper_factor + self.sigma) * median))

            auto_canny = cv2.Canny(img_8bit, lower, upper)

            # Salvar o resultado do Canny em um novo arquivo .tiff
            with rasterio.open(tif_path) as src:
                profile = src.profile  # Copie o perfil do NDWI
                profile.update(
                    dtype=rasterio.uint8, count=1
                )  # Atualize o tipo de dados e o número de bandas
                with rasterio.open(output_path, "w", **profile) as dst:
                    dst.write(auto_canny, 1)  # Escreva o resultado do Canny na banda 1

            logger.info(f"Resultado do Canny salvo como {output_path}")
        else:
            logger.error(f"Erro ao ler a imagem NDWI {tif_path}.")

