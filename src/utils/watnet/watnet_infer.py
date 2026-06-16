## author: xin luo, creat: 2021.8.11

"""
des: perform surface water mapping by using pretrained watnet
     through funtional api and command line, respectively.

example:
     funtional api:
        water_map = watnet_infer(rsimg)
     command line:
        python watnet_infer.py data/test-demo/*.tif
        python watnet_infer.py data/test-demo/*.tif -o data/test-demo/result
    note:
        rsimg is np.array (row,col,band), value: [0,1]
        data/test-demo/*.tif is the sentinel-2 image path
        data/test-demo/result is output directory
"""

import argparse
import gc
import os
from collections import defaultdict

import numpy as np
import rasterio
import tensorflow as tf
import tifffile as tiff

from utils.watnet.utils.imgPatch import imgPatch

## default path of the pretrained watnet model
path_watnet = "src/utils/watnet/model/pretrained/watnet.h5"


def get_args():
    description = "surface water mapping by using pretrained watnet"
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "ifile",
        metavar="ifile",
        type=str,
        nargs="+",
        help=("file(s) to process (.tiff)"),
    )

    parser.add_argument(
        "-m",
        metavar="watnet",
        dest="watnet",
        type=str,
        nargs="+",
        default=path_watnet,
        help=("pretrained watnet model (tensorflow2, .h5)"),
    )

    parser.add_argument(
        "-o",
        metavar="odir",
        dest="odir",
        type=str,
        nargs="+",
        help=("directory to write"),
    )

    return parser.parse_args()


def watnet_infer(image_path, save_path, path_model=path_watnet, patch_size=512):
    """des: surface water mapping by using pretrained watnet
    arg:
        img: np.array, surface reflectance data (!!data value: 0-1),
             consist of 6 bands (blue,green,red,nir,swir-1,swir-2).
        path_model: str, the path of the pretrained model.
    retrun:
        water_map: np.array.
    """
    ###  ----- load the pretrained model -----#
    model = tf.keras.models.load_model(path_model, compile=False)
    ### ------ apply the pre-trained model
    image = tiff.imread(image_path) / 10000.0  # normalize the image data to [0, 1]
    image = image[
        :, :, [1, 2, 3, 7, 10, 11]
    ]  # select bands Blue, Green, Red, NIR, SWIR1, SWIR2

    imgPatch_ins = imgPatch(image, patch_size=patch_size, edge_overlay=80)
    patch_list, start_list, img_patch_row, img_patch_col = imgPatch_ins.toPatch()
    result_patch_list = [model(patch[np.newaxis, :]) for patch in patch_list]
    result_patch_list = [np.squeeze(patch, axis=0) for patch in result_patch_list]
    pro_map = imgPatch_ins.toImage(result_patch_list, img_patch_row, img_patch_col)
    pro_map_uint8 = (pro_map * 255).astype(np.uint8)

    # water_map = np.where(pro_map >= 0.5, 1, 0)

    with rasterio.open(image_path) as src:
        profile = src.profile
        profile.update(count=1, dtype=rasterio.float32)
        with rasterio.open(save_path, "w", **profile) as output:
            output.write(np.squeeze(pro_map), 1)

            # del model
            del image
            del output

            gc.collect()

    return pro_map


def watnet_infer_optimized(
    image_paths, save_path, path_model=path_watnet, patch_size=512
):
    all_patches = []  # lista com todos os patches
    metadata = []  # lista com informações do patch

    model = tf.keras.models.load_model(path_model, compile=False)

    for img_path in image_paths:
        image = tiff.imread(img_path) / 10000.0
        image = image[:, :, [1, 2, 3, 7, 10, 11]]

        patcher = imgPatch(image, patch_size=512, edge_overlay=80)
        patches, starts, n_rows, n_cols = patcher.toPatch()

        for idx, patch in enumerate(patches):
            all_patches.append(patch)
            metadata.append(
                {
                    "image_name": os.path.basename(img_path),
                    "index": idx,
                    "n_rows": n_rows,
                    "n_cols": n_cols,
                    "start_coords": starts[idx],
                    "patcher": patcher,  # salvar referência para reconstrução
                }
            )

    batch_size = 32
    all_preds = []

    for i in range(0, len(all_patches), batch_size):
        batch = np.stack(all_patches[i : i + batch_size], axis=0)
        preds = model(batch, training=False).numpy()
        all_preds.extend(preds)

    results_by_image = defaultdict(list)

    for i, meta in enumerate(metadata):
        key = meta["image_name"]
        results_by_image[key].append((meta["index"], all_preds[i], meta))

    for image_name, results in results_by_image.items():
        # Ordenar os patches para garantir ordem correta
        results.sort(key=lambda x: x[0])  # x[0] é o índice do patch

        patches = [r[1] for r in results]
        patcher = results[0][2]["patcher"]
        n_rows = results[0][2]["n_rows"]
        n_cols = results[0][2]["n_cols"]

        full_image = patcher.toImage(patches, n_rows, n_cols)

        # Salvar com rasterio
        original_path = [p for p in image_paths if os.path.basename(p) == image_name][0]
        file_path = os.path.join(save_path, image_name)

        with rasterio.open(original_path) as src:
            profile = src.profile
            profile.update(count=1, dtype=rasterio.float32)
            with rasterio.open(file_path, "w", **profile) as dst:
                dst.write(np.squeeze(full_image), 1)


def watnet_infer_batch(
    image_paths,
    save_paths,
    model,
    patch_size=512,
    edge_overlay=80,
    batch_size=16,
    bands=(1, 2, 3, 7, 10, 11),
):
    """
    Inferência batch para múltiplas imagens com divisão em patches.

    Args:
        image_paths (list[str]): caminhos das imagens de entrada
        save_paths (list[str]): caminhos para salvar os resultados
        model (tf.keras.Model): modelo já carregado
        patch_size (int): tamanho dos patches
        edge_overlay (int): sobreposição entre patches
        batch_size (int): batch usado na inferência
        bands (tuple): índices das bandas a serem usadas

    Returns:
        list[np.array]: mapas de probabilidade reconstruídos
    """

    assert len(image_paths) == len(save_paths), (
        "image_paths e save_paths devem ter o mesmo tamanho"
    )

    all_patches = []
    metadata = []

    # =========================================
    # 1. GERAR PATCHES DE TODAS AS IMAGENS
    # =========================================
    for img_idx, image_path in enumerate(image_paths):
        # leitura e normalização
        image = tiff.imread(image_path).astype(np.float32) / 10000.0
        # TODO: permitir escolher bandas
        # image = image[:, :, bands]

        # gerar patches
        patcher = imgPatch(image, patch_size=patch_size, edge_overlay=edge_overlay)

        patch_list, _, n_rows, n_cols = patcher.toPatch()

        all_patches.extend(patch_list)

        metadata.append(
            {
                "patcher": patcher,
                "num_patches": len(patch_list),
                "rows": n_rows,
                "cols": n_cols,
                "image_path": image_path,
                "save_path": save_paths[img_idx],
            }
        )

        del image  # liberar RAM

    # =========================================
    # 2. INFERÊNCIA EM BATCH GLOBAL
    # =========================================
    all_patches = np.stack(all_patches)  # (total_patches, H, W, C)

    preds = model.predict(all_patches, batch_size=batch_size, verbose=0)

    # =========================================
    # 3. RECONSTRUÇÃO DAS IMAGENS
    # =========================================
    results = []
    cursor = 0

    for meta in metadata:
        n = meta["num_patches"]

        preds_subset = preds[cursor : cursor + n]
        cursor += n

        pro_map = meta["patcher"].toImage(preds_subset, meta["rows"], meta["cols"])

        pro_map = np.squeeze(pro_map)

        # salvar resultado mantendo metadados geoespaciais
        with rasterio.open(meta["image_path"]) as src:
            profile = src.profile
            profile.update(count=1, dtype=rasterio.float32)

            with rasterio.open(meta["save_path"], "w", **profile) as dst:
                dst.write(pro_map.astype(np.float32), 1)

        results.append(pro_map)

    # limpeza
    del all_patches
    del preds
    gc.collect()

    return results


import gc

import numpy as np
import onnxruntime as ort
import rasterio
import tifffile as tiff


def configurar_sessao_cpu(onnx_path, num_threads=8):
    """Configura o ONNX para usar o máximo de núcleos da CPU."""
    options = ort.SessionOptions()
    # Ajuste para o número de cores reais do seu processador
    options.intra_op_num_threads = num_threads
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

    return ort.InferenceSession(
        onnx_path, sess_options=options, providers=["CPUExecutionProvider"]
    )


def watnet_infer_onnx_optimized(
    image_paths,
    save_paths,
    ort_session,
    patch_size=512,
    edge_overlay=80,
    batch_size=8,  # Na CPU, batches muito grandes (ex: 64) podem ser MAIS lentos
    bands=(1, 2, 3, 7, 10, 11),
):
    input_name = ort_session.get_inputs()[0].name
    output_name = ort_session.get_outputs()[0].name

    for img_path, save_path in zip(image_paths, save_paths):
        # 1. Leitura rápida
        image = tiff.imread(img_path).astype(np.float32) / 10000.0
        image = image[:, :, bands]

        patcher = imgPatch(image, patch_size=patch_size, edge_overlay=edge_overlay)
        patch_list, _, n_rows, n_cols = patcher.toPatch()

        # Aproveitando seus 32GB de RAM: Convertemos tudo de uma vez
        img_patches = np.array(patch_list, dtype=np.float32)
        del image, patch_list

        # 2. Inferência em CPU
        # Nota: Na CPU, batch_size entre 4 e 12 costuma ser o 'sweet spot'
        img_preds = []
        for i in range(0, len(img_patches), batch_size):
            batch = img_patches[i : i + batch_size]
            # O ONNX gerenciará o paralelismo interno nos núcleos da CPU
            batch_pred = ort_session.run([output_name], {input_name: batch})[0]
            img_preds.append(batch_pred)

        preds_combined = np.concatenate(img_preds, axis=0)

        # 3. Reconstrução e Salvamento
        pro_map = np.squeeze(patcher.toImage(preds_combined, n_rows, n_cols))

        with rasterio.open(img_path) as src:
            profile = src.profile
            profile.update(count=1, dtype=rasterio.float32, nodata=0, compress="lzw")
            with rasterio.open(save_path, "w", **profile) as dst:
                dst.write(pro_map.astype(np.float32), 1)

        # Limpeza para a próxima imagem
        del img_patches, img_preds, preds_combined, pro_map
        gc.collect()

    return True


def deepwatermap_infer_onnx(
    image_paths,
    save_paths,
    ort_session,
    threshold=0.5,
    bands=(1, 2, 3, 7, 10, 11),
):
    """
    Inferência do modelo DeepWaterMap convertido para ONNX,
    mantendo comportamento original (padding múltiplo de 32, soft threshold).
    """
    input_name = ort_session.get_inputs()[0].name
    output_name = ort_session.get_outputs()[0].name

    for img_path, save_path in zip(image_paths, save_paths):
        # 1. Leitura da imagem
        image = tiff.imread(img_path).astype(np.float32)
        # image = image[:, :, bands]

        # 2. Padding para múltiplos de 32
        pad_r = find_padding(image.shape[0])
        pad_c = find_padding(image.shape[1])
        image = np.pad(
            image, ((pad_r[0], pad_r[1]), (pad_c[0], pad_c[1]), (0, 0)), "reflect"
        )

        # Corrige casos em que pad final é 0
        if pad_r[1] == 0:
            pad_r = (pad_r[0], 1)
        if pad_c[1] == 0:
            pad_c = (pad_c[0], 1)

        # 3. Limpeza e normalização
        image = np.nan_to_num(image, copy=False, nan=0.0, posinf=0.0, neginf=0.0)
        image = image - np.min(image)
        image = image / np.maximum(np.max(image), 1)
        image = np.expand_dims(image, axis=0)

        # 4. Inferência ONNX
        pred = ort_session.run([output_name], {input_name: image})[0]
        pred = np.squeeze(pred)
        pred = pred[pad_r[0] : -pad_r[1], pad_c[0] : -pad_c[1]]

        # 5. Soft threshold + binarização
        pred = 1.0 / (1 + np.exp(-(16 * (pred - 0.5))))
        # pred_binary = (pred >= threshold).astype(np.uint8)

        # 6. Salvar saída
        with rasterio.open(img_path) as src:
            profile = src.profile
            profile.update(count=1, dtype=rasterio.float32)
            with rasterio.open(save_path, "w", **profile) as dst:
                dst.write(pred.astype(np.float32), 1)

        del image, pred
        gc.collect()

    return True


def find_padding(v, divisor=32):
    v_divisible = max(divisor, int(divisor * np.ceil(v / divisor)))
    total_pad = v_divisible - v
    pad_1 = total_pad // 2
    pad_2 = total_pad - pad_1
    return pad_1, pad_2
