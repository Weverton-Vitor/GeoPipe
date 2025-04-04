import glob
import logging
import os

import numpy as np
import rasterio as rio
import torch
import segmentation_models_pytorch as smp
import requests
from tqdm import tqdm
from PIL import Image

from utils.cloud_removal.bcl import BCL
from utils.unet.unet_utils import save_mask_tif, save_overlayed_mask_plot


logger = logging.getLogger(__name__)

def load_unet_model(model_path: str = None):
    # Se o arquivo não existir localmente, faça o download
    if model_path is None or not os.path.exists(model_path):
        model_url = "https://huggingface.co/datasets/isp-uv-es/CloudSEN12Plus/resolve/main/demo/models/UNetMobV2_V2.pt"
        model_path = "UNetMobV2_V2.pt"
        logger.info("Fazendo download do modelo UNet...")
        with requests.get(model_url, stream=True) as r:
            with open(model_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    
    # Cria o modelo e carrega os pesos
    model = smp.Unet(encoder_name="mobilenet_v2", encoder_weights=None, classes=4, in_channels=13)
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    
    # Desativa os gradientes e coloca o modelo em modo de avaliação
    for param in model.parameters():
        param.requires_grad = False
    model = model.eval()
    return model

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
    if skip_masks:
        logger.warning("Pular geração das máscaras com UNet")
        return True

    # Se parâmetros específicos do Unet forem fornecidos, extraia-os; caso contrário, use defaults
    if unet_params is None:
        unet_params = {}
    model_weights = unet_params.get("model_weights", None)
    # cloud_clear_class não será utilizado no remapeamento
    cloud_thick_class = unet_params.get("cloud_thick_class", 1)
    cloud_thin_class = unet_params.get("cloud_thin_class", 2)
    cloud_shadow_class = unet_params.get("cloud_shadow_class", 3)

    # Carrega o modelo (usando o caminho dos pesos fornecido, se disponível)
    model = load_unet_model(model_weights)

    # Encontra os arquivos TIFF (assegure que são imagens com 13 bandas)
    inputs = glob.glob(f"{toa_path}{location_name}/*/*.tif")
    
    for inp in tqdm(inputs, desc="Processando imagens com UNet"):
        inp = inp.replace("\\", "/")
        file_name = f"{location_name}/{inp.split('/')[-2]}/unet_mask_{inp.split('/')[-1].split('.')[0]}"
        
        # Abre a imagem com Rasterio e normaliza os valores
        with rio.open(inp) as src:
            image_array = src.read()  # shape: (bands, height, width)
            image_array = image_array / 10_000
        
        if image_array.shape[0] != 13:
            logger.error(f"Imagem {inp} não possui 13 canais. Verifique os dados de entrada.")
            continue
        
        # Converte a imagem para tensor (adiciona a dimensão do batch)
        input_tensor = torch.from_numpy(image_array).unsqueeze(0).float()
        
        # Realiza a inferência e obtém a máscara com 4 classes
        with torch.no_grad():
            output = model(input_tensor)
            segmentation_mask = output.argmax(dim=1).numpy().squeeze()
        
        # Remapeamento:
        # - Atribui 1 aos pixels classificados como nuvem (tanto grossa quanto fina)
        # - Atribui 2 aos pixels classificados como sombra de nuvem
        # - O restante permanece 0 (céu limpo)
        remapped_mask = np.zeros_like(segmentation_mask, dtype=np.uint8)
        remapped_mask[np.isin(segmentation_mask, [cloud_thick_class, cloud_thin_class])] = 1
        remapped_mask[segmentation_mask == cloud_shadow_class] = 2
        
        # Salva a máscara remapeada (visualização e TIFF) usando funções adaptadas para Unet
        save_overlayed_mask_plot(
            remapped_mask, output_file=f"{save_plots_path}{file_name}.png"
        )
        save_mask_tif(
            remapped_mask, original_tif_file=inp, output_file=f"{save_masks_path}{file_name}.tif"
        )

    return True

def cloud_removal(
    path_images: str,
    path_masks: str,
    output_path: str,
    location_name: str,
    cloud_and_cloud_shadow_pixels: list,
    init_date: str,
    final_date: str,
    skip_clean: bool,
    color_file_log_path: str,
    *args,
    **kwargs,
):
    if skip_clean:
        logger.warning("Skip Cloud Removal")
        return True

    logger.info(f"Executando reservatório {location_name}.")

    year_range = range(int(init_date.split("-")[0]), int(final_date.split("-")[0]) + 1)

    tif_files = glob.glob(os.path.join(path_images, "**", "*.tif"), recursive=True)
    total_tifs = len(tif_files)

    with tqdm(total=total_tifs, desc="Cleaning Images", unit="file") as pbar:
        for year in year_range:
            path_images_year = f"{path_images}{location_name}/{year}/"
            path_masks_year = f"{path_masks}{location_name}/{year}/"
            color_file_log = f"{color_file_log_path}{location_name}/{year}/"

            for image in os.listdir(path_images_year):
                image_path = os.path.join(path_images_year, image)
                if not image.lower().endswith(".tif"):
                    continue

                # Obtém as dimensões da imagem
                with rio.open(image_path) as tiff:
                    image_tiff = tiff.read()
                size = image_tiff.shape[1], image_tiff.shape[2]

                # Obtenção da data a partir do nome do arquivo
                date = image.split("_")[-1].split(".")[0].replace("-", "")

                # Certifique-se de que a classe BCL está importada corretamente no seu módulo
                i = BCL(
                    img_dim=size,
                    scl_path=path_masks_year,
                    path_6B=path_images_year,
                    year=year,
                    data=date,
                    intern_reservoir=location_name,
                    cloud_pixels=cloud_and_cloud_shadow_pixels,
                    use_dec_tree=False,
                    color_file_path=color_file_log,
                )

                # Realiza a correção
                try:
                    i.singleImageCorrection(
                        date,
                        year,
                        f"{output_path}{location_name}/{year}/",
                        image.replace(".tif", ""),
                    )
                except Exception as e:
                    logger.error(e)
                    continue

                pbar.update(1)
                i.death()

    return True
