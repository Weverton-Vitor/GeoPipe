import datetime
import logging
import os
import warnings
from datetime import datetime as dt

import cv2
import numpy as np
import rasterio as TIFF
from matplotlib import pyplot as plt
from PIL import Image as img

# Suprime todos os warnings
# warnings.filterwarnings("ignore", category=UserWarning, module="rasterio")
logging.getLogger("rasterio").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


class BCL:
    def __init__(
        self,
        img_dim,
        time_series_masks_path,
        time_series_images_path,
        year,
        data,
        intern_reservoir,
        cloud_pixels,
        use_dec_tree,
        color_file_path,
    ):
        self.intern_reservoir = intern_reservoir
        self.width, self.height = img_dim
        self.time_series_masks_path = time_series_masks_path
        self.time_series_images_path = time_series_images_path
        self.year = year
        self.nuvem = cloud_pixels
        self.idx_class_cloud = 0
        # self.color_file = open(f"{color_file_path}color_file_{data}.txt", "w")

        self.original_image_mask = None
        self.original_image_mask_meta = None

        self.original_image = None
        self.original_image_meta = None

    def death(self):
        del self

    def pxHasCloud(self, pixelValue):
        return pixelValue in self.nuvem

    def openImageAndMask(self, image_path, mask_path):
        with TIFF.open(mask_path) as mask:
            self.original_image_mask = mask.read()
            self.original_image_mask_meta = mask.meta

        with TIFF.open(image_path) as image:
            self.original_image = image.read()
            self.original_image_meta = image.meta

        # print(image_path)
        # print(self.original_image.shape)

        # print(mask_path)
        # print(self.original_image_mask.shape)

        # se alguma das duas imagens são vazias, lança exceção
        if self.original_image.shape[0] == 0 or self.original_image_mask.shape[0] == 0:
            raise Exception("Erro")

        # Cria uma matriz booleana onde True indica que o pixel está poluído
        # Essa imagem é grayscale, cada cor imagem que for usada será uma cor diferente
        # sempre que um pixel de uma imagem for utilizado, essa máscara será marcada na mesma localização com a cor da imagem
        self.mask = np.zeros(
            (
                self.original_image_mask.shape[1],
                self.original_image_mask.shape[2],
            ),
            dtype=np.uint8,
        )

    # Os pixels que já estiverem 'limpos' serão mantidos
    # Aqueles que estão com nuvens ou sombras serão marcados em memória.
    def alreadyClear(self):
        # Cria uma matriz booleana onde True indica que o pixel está poluído
        cloud_mask = np.isin(self.original_image_mask[self.idx_class_cloud], self.nuvem)

        # Cria uma máscara onde True indica que o pixel está limpo
        clear_mask = ~cloud_mask

        # Transfere os pixels limpos para o resultado
        self.resultadoIMGSCL[0][clear_mask] = self.original_image_mask[
            self.idx_class_cloud
        ][clear_mask]

        # print('------------')
        # print(self.original_image_mask.shape)
        # print(clear_mask.shape)
        # print(self.resultadoIMGNDWI.shape)
        for i in range(len(self.resultadoIMGNDWI)):
            self.resultadoIMGNDWI[i][clear_mask] = self.original_image[i][clear_mask]
        self.mask[clear_mask] = [0]
        # self.color_file.write("0 is the actual color of the image\n")

    # Função que carrega em memória todas as imagens do ano
    def getAllImagesYear(self, data):
        self.imagesSclOfTheYear = []
        for image in [
            f for f in os.listdir(self.time_series_masks_path) if f.endswith(".tif")
        ]:
            if image.replace("-", "").find(data) != -1:
                continue
            else:
                self.imagesSclOfTheYear.append(image)

    # Função responsável por receber uma data e
    def relativeTime(self, init_date):
        # Converte a data para o formato datetime
        data1 = dt.strptime(init_date, "%Y%m%d")

        self.relativeTimeList, self.pairImages = [], []

        for imagem in self.imagesSclOfTheYear:
            if init_date in imagem:
                continue

            # Obtém a data da imagem
            size_init_path = len(self.intern_reservoir + "_")
            date = imagem.split("_")[-1].split(".")[0].replace("-", "")

            # print(f"Date = {date}")

            formated_date = dt.strptime(date, "%Y%m%d")

            # Calcula a distância entre as datas e salva na lista
            self.relativeTimeList.append(abs((formated_date - data1).days))
            self.pairImages.append(imagem)
        return self.pairImages

    # Nesta função é gerada a imagem
    def subPorDataProx(self, year, just_that=True):
        # print("Iniciando correção temporal...")
        # Cada imagem será uma lista, em que o primeiro elemento é o nome da imagem
        # e os demais são os pixels que podem ser utilizados para a correção temporal
        self.elementos = [[] for _ in range(len(self.imagesSclOfTheYear))]

        # Essa imagem é grayscale, cada cor imagem que for usada será uma cor diferente
        # sempre que um pixel de uma imagem for utilizado, essa máscara será marcada na mesma localização com a cor da imagem
        self.mask = np.zeros(
            (
                self.original_image_mask.shape[1],
                self.original_image_mask.shape[2],
                3,
            ),
            dtype=np.uint8,
        )

        # Pixels de valores altearios
        color = 5

        dict_color_image = {}

        # Para cada slot
        for i, _ in enumerate(self.elementos):
            # Índice de imagem mais próxima
            i_image_more_closer = self.relativeTimeList.index(
                min(self.relativeTimeList)
            )
            path_image_more_close_scl = (
                self.time_series_masks_path + self.pairImages[i_image_more_closer]
            )

            # Filtro para obter a data da imagem
            date = (
                self.pairImages[i_image_more_closer]
                .split("_")[-1]
                .split(".")[0]
                .replace("-", "")
            )

            image_more_close_6b = None
            for i6b in [
                f
                for f in os.listdir(self.time_series_images_path)
                if f.endswith(".tif")
            ]:
                if i6b.replace("-", "").find(date) != -1:
                    with TIFF.open(self.time_series_images_path + i6b) as tiff:
                        image_more_close_6b = tiff.read()
                        # print('------')
                            # print(self.time_series_images_path + i6b)
                        break

            # A imagem mais próxima é carregada
            with TIFF.open(path_image_more_close_scl) as tiff:
                image_more_close_scl = tiff.read()
                array_image_more_close_scl = image_more_close_scl[0]

            # O primeiro elemento da lista é o nome da imagem
            self.elementos[i].append(self.pairImages[i_image_more_closer])
            self.relativeTimeList[i_image_more_closer] = (
                50000  # Aqui ela deixa de ser a mais próxima na próxima iteração
            )

            # Onde na imagem é pixel limpo e nos resultados ainda é -1, é substituído o pixel poluído pelo limpo
            mask1 = np.logical_not(np.isin(array_image_more_close_scl, self.nuvem))
            mask2 = self.resultadoIMGSCL[0] == -1

            # print(mask1.shape)
            # print(mask2.shape)

            # print('------------')
            # print(path_image_more_close_scl)
            # print(image_more_close_scl[0].shape)

            # se mask2 não tiver nenhum pixel -1, não há mais pixels para serem substituídos
            if not np.any(mask2):
                break

            # 1. Cria a máscara combinada uma única vez para economizar processamento
            mask_combinada = mask1 & mask2

            # 2. Mantém a primeira atribuição idêntica
            self.resultadoIMGSCL[0][mask_combinada] = array_image_more_close_scl[
                mask_combinada
            ]

            if image_more_close_6b is None:
                logger.warning(
                    "No corresponding 6-band image found for '%s'. Skipping band update.",
                    self.pairImages[i_image_more_closer],
                )
                continue
            
            # print('------------')
            # print(mask_combinada.shape)
            # print(self.resultadoIMGNDWI.shape)
            # print(image_more_close_6b.shape)
            # 3. Atualiza as 12 bandas de uma só vez (índices de 0 a 11)
            self.resultadoIMGNDWI[0 : len(self.resultadoIMGNDWI), mask_combinada] = (
                image_more_close_6b[0 : len(self.resultadoIMGNDWI), mask_combinada]
            )

            # Color[i] is like [255 255 255], so it is necessary to convert px format [255,255,255]
            if color < 255:
                color += 5

            self.mask[mask1 & mask2] = [color]
            dict_color_image[str(color)] = self.pairImages[i_image_more_closer]

        if just_that:
            # onde for -1, não foi possível substituir o pixel
            # então será atribuído o valor original da imagem
            self.resultadoIMGSCL[0][(self.resultadoIMGSCL[0] == -1)] = (
                self.original_image_mask[self.idx_class_cloud][
                    (self.resultadoIMGSCL[0] == -1)
                ]
            )

            for i in range(12):
                self.resultadoIMGNDWI[i][(self.resultadoIMGNDWI[i] == -1)] = (
                    self.original_image[i][(self.resultadoIMGNDWI[i] == -1)]
                )

            self.mask[self.resultadoIMGSCL[0] == -1] = [0]

            dict_color_image[str([0])] = "could no be corrected"

        # for key, value in dict_color_image.items():
        #     self.color_file.write(f"{key} is the color of {value}\n")

    def singleImageCorrection(
        self,
        target_image_path,
        target_mask_path,
        output_path,
        image_date,
        image_year,
        just_sp=False,
    ):
        self.openImageAndMask(target_image_path, target_mask_path)

        # os resultados são inicialmente arrays de -1
        self.resultadoIMGSCL = np.full(
            (
                1,
                self.original_image_mask.shape[1],
                self.original_image_mask.shape[2],
            ),
            -1,
            dtype=np.int16,
        )
        self.resultadoIMGNDWI = np.full(
            (
                self.original_image.shape[0],
                self.original_image.shape[1],
                self.original_image.shape[2],
            ),
            -1,
            dtype=np.int16,
        )

        # print(self.resultadoIMGNDWI.shape)
        # print(self.resultadoIMGSCL.shape)
        # print("")
        # print(target_image_path)
        # print(target_mask_path)
        # print(self.time_series_images_path)
        # print(self.time_series_masks_path)

        # # # Salva os pixels que estão poluídos
        self.alreadyClear()
        self.getAllImagesYear(image_date)

        # Correção temporal
        self.relativeTime(image_date)
        self.subPorDataProx(image_year, just_sp)

        # # self.correcaoPorBorda(3, 3)
        self.resultadoIMGSCL = np.where(
            self.resultadoIMGSCL == -1, 0, self.resultadoIMGSCL
        )
        self.resultadoIMGNDWI = np.where(
            self.resultadoIMGNDWI == -1, 0, self.resultadoIMGNDWI
        )

        # Salvando novo arquivo com resultado e rasterio
        # cv2.imwrite(scl_output_path + "/" + data + "_mask.png", self.resultadoIMGSCL[0])
        with TIFF.open(
            f"{output_path}{target_image_path.split('/')[-1].split('.')[0]}_clean.tif",
            "w",
            **self.original_image_meta,
        ) as dst:
            dst.write(self.resultadoIMGNDWI)
