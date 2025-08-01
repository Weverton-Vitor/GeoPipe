
## author: xin luo, creat: 2021.8.11

'''
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
'''

import argparse
import gc
import os

import numpy as np
import rasterio
import tensorflow as tf
import tifffile as tiff
from collections import defaultdict

from utils.watnet.utils.imgPatch import imgPatch

## default path of the pretrained watnet model
path_watnet = 'src/utils/watnet/model/pretrained/watnet.h5'

def get_args():

    description = 'surface water mapping by using pretrained watnet'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        'ifile', metavar='ifile', type=str, nargs='+',
        help=('file(s) to process (.tiff)'))

    parser.add_argument(
        '-m', metavar='watnet', dest='watnet', type=str, 
        nargs='+', default=path_watnet, 
        help=('pretrained watnet model (tensorflow2, .h5)'))

    parser.add_argument(
        '-o', metavar='odir', dest='odir', type=str, nargs='+', 
        help=('directory to write'))

    return parser.parse_args()




def watnet_infer(image_path, save_path, path_model = path_watnet, patch_size=512):

    ''' des: surface water mapping by using pretrained watnet
        arg:
            img: np.array, surface reflectance data (!!data value: 0-1), 
                 consist of 6 bands (blue,green,red,nir,swir-1,swir-2).
            path_model: str, the path of the pretrained model.
        retrun:
            water_map: np.array.
    '''
    ###  ----- load the pretrained model -----#
    model = tf.keras.models.load_model(path_model, compile=False)
    ### ------ apply the pre-trained model
    image = tiff.imread(image_path) / 10000.0  # normalize the image data to [0, 1]
    image = image[:, :, [1, 2, 3, 7, 10, 11]]  # select bands Blue, Green, Red, NIR, SWIR1, SWIR2

    imgPatch_ins = imgPatch(image, patch_size=patch_size, edge_overlay=80)
    patch_list, start_list, img_patch_row, img_patch_col = imgPatch_ins.toPatch()
    result_patch_list = [model(patch[np.newaxis, :]) for patch in patch_list]
    result_patch_list = [np.squeeze(patch, axis = 0) for patch in result_patch_list]
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


def watnet_infer_optimized(image_paths, save_path, path_model = path_watnet, patch_size=512):
    all_patches = []           # lista com todos os patches
    metadata = []              # lista com informações do patch

    model = tf.keras.models.load_model(path_model, compile=False)

    for img_path in image_paths:
        image = tiff.imread(img_path) / 10000.0
        image = image[:, :, [1,2,3,7,10,11]]
        
        patcher = imgPatch(image, patch_size=512, edge_overlay=80)
        patches, starts, n_rows, n_cols = patcher.toPatch()
        
        for idx, patch in enumerate(patches):
            all_patches.append(patch)
            metadata.append({
                "image_name": os.path.basename(img_path),
                "index": idx,
                "n_rows": n_rows,
                "n_cols": n_cols,
                "start_coords": starts[idx],
                "patcher": patcher,  # salvar referência para reconstrução
            })


    batch_size = 32
    all_preds = []

    for i in range(0, len(all_patches), batch_size):
        batch = np.stack(all_patches[i:i+batch_size], axis=0)
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
