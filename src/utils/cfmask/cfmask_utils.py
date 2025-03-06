import os

import numpy as np
import rasterio
import tifffile as tiff
import logging

from utils.fmask.fmask_utils import read_bands

logger = logging.getLogger(__name__)


def get_mask(val, typ="cloud"):
    """Get mask for a specific cover type"""

    # convert to binary
    bin_ = "{0:016b}".format(val)

    # reverse string
    str_bin = str(bin_)[::-1]

    # get bit for cover type
    bits = {"cloud": 3, "shadow": 4, "dilated_cloud": 1, "cirrus": 2}
    bit = str_bin[bits[typ]]

    if bit == "1":
        return 0  # cover
    else:
        return 1  # no cover


def get_binary_mask_from_path(image_path, qa_index=-1, bgr_index=[0, 1, 2]):
    all_bands = read_bands(image_path)

    rgb_composite = np.transpose(
        np.array(
            [
                all_bands[bgr_index[0]],  # R
                all_bands[bgr_index[1]],  # G
                all_bands[bgr_index[2]],  # B
            ]
        ),
        [1, 2, 0],
    )

    # QA_Pixel é a ultima banda, mas é possível alterar usando qa_index
    qa_pixel = np.array(all_bands[qa_index])

    bits = {"cloud": 3, "dilated_cloud": 1, "cirrus": 2, "shadow": 4, "water": 7}

    cloud_mask = ((qa_pixel & (1 << bits["cloud"])) > 0).astype(np.uint8)
    dilated_cloud_mask = ((qa_pixel & (1 << bits["dilated_cloud"])) > 0).astype(
        np.uint8
    )
    cirrus_mask = ((qa_pixel & (1 << bits["cirrus"])) > 0).astype(np.uint8)
    final_shadow_mask = ((qa_pixel & (1 << bits["shadow"])) > 0).astype(np.uint8)
    water_mask = ((qa_pixel & (1 << bits["water"])) > 0).astype(np.uint8)
    final_cloud_mask = (cloud_mask | dilated_cloud_mask | cirrus_mask).astype(np.uint8)

    return {
        "rgb_composite": rgb_composite,
        "cloud_mask": final_cloud_mask,
        "shadow_cloud_mask": final_shadow_mask,
        "water_mask": water_mask,
    }
