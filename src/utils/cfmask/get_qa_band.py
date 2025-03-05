import os

import numpy as np
import tifffile as tiff


def get_mask(val, type="cloud"):
    """Get mask for a specific cover type"""

    # convert to binary
    bin_ = "{0:016b}".format(val)

    # reverse string
    str_bin = str(bin_)[::-1]

    # get bit for cover type
    bits = {"cloud": 3, "shadow": 4, "dilated_cloud": 1, "cirrus": 2}
    bit = str_bin[bits[type]]

    if bit == "1":
        return 0  # cover
    else:
        return 1  # no cover


def get_binary_mask_from_path(image_path, qa_index=-1, bgr_index=[0, 1, 2]):
    all_bands = tiff.imread(image_path)

    # QA_Pixel é sempre a ultima banda
    qa_pixel = np.array(all_bands[:, :, qa_index])

    cloud_mask = np.vectorize(get_mask)(qa_pixel, type="cloud")
    shadow_mask = np.vectorize(get_mask)(qa_pixel, type="shadow")
    dilated_cloud_mask = np.vectorize(get_mask)(qa_pixel, type="dilated_cloud")
    cirrus_mask = np.vectorize(get_mask)(qa_pixel, type="cirrus")

    # segmentation image
    seg = np.dstack(
        (
            all_bands[:, :, bgr_index[0]],  # B
            all_bands[:, :, bgr_index[1]],  # G
            all_bands[:, :, bgr_index[2]],  # R
        )
    )

    # color for mask (white)
    mask_color = np.array([255, 255, 255])
    masks = [cloud_mask, shadow_mask, dilated_cloud_mask, cirrus_mask]

    # create a black image with the same size as the original
    mask_image = np.zeros_like(seg)

    for mask in masks:
        # apply mask color
        mask_image[mask == 0] = mask_color

    path_scl = image_path.replace("6B", "SLC")
    save_full_path = path_scl.replace(".tif", ".png")
    # print()
    # save the mask image
    if not os.path.exists(save_full_path[:-19]):
        os.makedirs(save_full_path[:-19])
    # cv2.imwrite(save_full_path, mask_image)
