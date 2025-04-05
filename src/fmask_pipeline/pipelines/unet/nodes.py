import glob
import logging
import os
from pathlib import Path

import numpy as np
import torch
import rasterio
import segmentation_models_pytorch as smp
import requests
from tqdm import tqdm

from rasterio import open as rio_open
from utils.cloud_removal.bcl import BCL
from utils.fmask.fmask_utils import save_mask_tif, save_overlayed_mask_plot

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
        encoder_name="mobilenet_v2",
        encoder_weights=None,
        classes=4,
        in_channels=13
    )
    # Carrega os pesos do modelo
    state_dict = torch.load(str(model_path), map_location=torch.device("cpu"))
    model.load_state_dict(state_dict)

    # Desativa os gradientes e coloca o modelo em modo de avaliação
    for param in model.parameters():
        param.requires_grad = False
    model.eval()
    return model

def apply_unet(
    toa_path: str,
    location_name: str,
    save_masks_path: str,
    save_plots_path: str,
    skip_masks: bool = False,
    model_path: str = None,
    unet_params: dict = None,
    water_masks_path: str = None,
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
        water_masks_path (str, opcional): Caminho das máscaras de água, se houver. Default é None.
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

    for inp in tqdm(inputs, desc="Processando imagens com UNet"):
        inp = inp.resolve()
        # Define o nome do arquivo de saída com base na estrutura de diretórios
        file_parts = inp.parts[-2:]
        file_name = f"{location_name}/{file_parts[0]}/unet_mask_{inp.stem}"

        # Abre a imagem e normaliza os valores
        try:
            with rio_open(str(inp)) as src:
                image_array = src.read()  # (bands, height, width)
                image_array = image_array / 10000.0
        except Exception as e:
            logger.error(f"Erro ao abrir a imagem {inp}: {e}")
            continue

        if image_array.shape[0] != 13:
            logger.error(f"Imagem {inp} não possui 13 canais. Verifique os dados de entrada.")
            continue

        # Converte a imagem para tensor e realiza a inferência
        input_tensor = torch.from_numpy(image_array).unsqueeze(0).float()
        with torch.no_grad():
            output = model(input_tensor)
            segmentation_mask = output.argmax(dim=1).numpy().squeeze()

        # Cria máscaras separadas para nuvem e sombra
        cloud_mask = np.zeros_like(segmentation_mask, dtype=np.uint8)
        cloud_mask[np.isin(segmentation_mask, [cloud_thick_class, cloud_thin_class])] = 1

        cloud_shadow_mask = np.zeros_like(segmentation_mask, dtype=np.uint8)
        cloud_shadow_mask[segmentation_mask == cloud_shadow_class] = 1

        # Tenta carregar a máscara de água, se o caminho for fornecido
        if water_masks_path:
            water_mask_file = Path(water_masks_path, location_name, inp.parts[-2], inp.name)
            if water_mask_file.exists():
                try:
                    with rasterio.open(str(water_mask_file)) as wsrc:
                        water_mask = wsrc.read(1).astype(np.uint8)
                except Exception as e:
                    logger.error(f"Erro ao ler máscara de água {water_mask_file}: {e}")
                    water_mask = np.zeros_like(segmentation_mask, dtype=np.uint8)
            else:
                water_mask = np.zeros_like(segmentation_mask, dtype=np.uint8)
        else:
            water_mask = np.zeros_like(segmentation_mask, dtype=np.uint8)

        # Gera uma composição colorida para o plot utilizando as bandas 4, 3 e 2 (índices 3, 2, 1)
        color_composite = image_array[[3, 2, 1], :, :]
        color_composite = np.transpose(color_composite, (1, 2, 0))  # (H, W, 3)

        # Garante que os diretórios de saída existam
        output_png = Path(save_plots_path, f"{file_name}.png")
        output_png.parent.mkdir(parents=True, exist_ok=True)
        output_tif = Path(save_masks_path, f"{file_name}.tif")
        output_tif.parent.mkdir(parents=True, exist_ok=True)

        # Salva o plot com as máscaras sobrepostas
        save_overlayed_mask_plot(
            masks=[cloud_mask, cloud_shadow_mask, water_mask],
            color_composite=color_composite,
            output_file=str(output_png)
        )

        # Salva o TIF com as 3 classes (1=nuvem, 2=sombra, 3=água)
        save_mask_tif(
            cloud_mask=cloud_mask,
            cloud_shadow_mask=cloud_shadow_mask,
            water_mask=water_mask,
            original_tif_file=str(inp),
            output_file=str(output_tif)
        )

    return True

def cloud_removal(
    path_images: str,
    path_masks: str,
    output_path: str,
    location_name: str,
    cloud_and_cloud_shadow_pixels: str,
    init_date: str,
    final_date: str,
    skip_clean: bool,
    color_file_log_path: str,
    *args,
    **kwargs,
):
    """
    Realiza a remoção de nuvens e sombras utilizando o algoritmo BCL.

    Args:
        path_images (str): Caminho base das imagens.
        path_masks (str): Caminho base para as máscaras.
        output_path (str): Caminho de saída para as imagens corrigidas.
        location_name (str): Nome do local ou reservatório.
        cloud_and_cloud_shadow_pixels (str): Parâmetro para definição de pixels de nuvem e sombra.
        init_date (str): Data inicial no formato 'YYYY-MM-DD'.
        final_date (str): Data final no formato 'YYYY-MM-DD'.
        skip_clean (bool): Se True, pula o processo de remoção de nuvens.
        color_file_log_path (str): Caminho para salvar os logs de cores.
    """
    if skip_clean:
        logger.warning("Skip Cloud Removal")
        return True

    logger.info(f"Executando remoção de nuvens para {location_name}.")

    start_year = int(init_date.split("-")[0])
    end_year = int(final_date.split("-")[0])
    year_range = range(start_year, end_year + 1)

    # Procura todos os arquivos TIFF de forma recursiva
    tif_files = glob.glob(os.path.join(path_images, "**", "*.tif"), recursive=True)
    total_tifs = len(tif_files)

    with tqdm(total=total_tifs, desc="Cleaning Images", unit="file") as pbar:
        for year in year_range:
            path_images_year = Path(path_images, location_name, str(year))
            path_masks_year = Path(path_masks, location_name, str(year))
            color_file_log = Path(color_file_log_path, location_name, str(year))
            color_file_log.mkdir(parents=True, exist_ok=True)

            # Processa cada imagem no diretório do ano
            for image in os.listdir(path_images_year):
                image_path = path_images_year / image
                try:
                    with rasterio.open(str(image_path)) as src:
                        image_tiff = src.read()
                except Exception as e:
                    logger.error(f"Erro ao ler a imagem {image_path}: {e}")
                    continue

                # Define o tamanho da imagem (height, width)
                size = (image_tiff.shape[1], image_tiff.shape[2])

                # Extrai a data do nome do arquivo
                date = image.split("_")[-1].split(".")[0].replace("-", "")

                # Instancia a classe BCL para correção
                bcl_instance = BCL(
                    img_dim=size,
                    scl_path=str(path_masks_year),
                    path_6B=str(path_images_year),
                    year=year,
                    data=date,
                    intern_reservoir=location_name,
                    cloud_pixels=cloud_and_cloud_shadow_pixels,
                    use_dec_tree=False,
                    color_file_path=str(color_file_log),
                )

                try:
                    bcl_instance.singleImageCorrection(
                        date,
                        year,
                        os.path.join(output_path, location_name, str(year)) + os.sep,
                        image.replace(".tif", ""),
                    )
                except Exception as e:
                    logger.error(f"Erro na correção da imagem {image}: {e}")
                    continue

                pbar.update(1)
                bcl_instance.death()

    return True