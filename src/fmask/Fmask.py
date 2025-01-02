import os

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageFilter

from fmask.fmask_utils import (
    calculate_brightness_temperature,
    calculate_flood_fill_transformation,
    calculate_ndsi,
    calculate_ndvi,
    calculate_ndwi,
    read_bands,
    save_mask_tif,
    save_overlayed_mask_plot,
)


class Fmask:
    def __init__(self, scale_factor):
        self.scale_factor = scale_factor

    def basic_test(self, swir2, bt, ndvi, ndsi) -> np.ndarray:
        """_summary_

        Args:
            b7 (_type_): _description_
            bt (_type_): _description_
            ndvi (_type_): _description_
            ndsi (_type_): _description_

        Returns:
            np.ndarray: _description_
        """

        # Eq. 1
        # bt = calculate_brightness_temperature(b6, 607.76, 1260.56, to_celsius=True)
        result = np.logical_and(swir2 > 0.03, bt < 27)
        result = np.logical_and(result, ndvi < 0.8)
        result = np.logical_and(result, ndsi < 0.8)

        return result

    def calculate_mean_visible(
        self, red: np.ndarray, green: np.ndarray, blue: np.ndarray
    ) -> np.ndarray:
        """_summary_

        Args:
            b3 (np.ndarray): _description_
            b2 (np.ndarray): _description_
            b1 (np.ndarray): _description_

        Returns:
            np.ndarray: _description_
        """

        return (red + green + blue) / 3

    def whiteness_test(
        self, red: np.ndarray, green: np.ndarray, blue: np.ndarray
    ) -> np.ndarray:
        """_summary_

        Args:
            b3 (np.ndarray): _description_
            b2 (np.ndarray): _description_
            b1 (np.ndarray): _description_

        Returns:
            np.ndarray: _description_
        """

        # Eq. 2
        bands = np.array([red, green, blue]).astype(np.float64)
        mean_visible = self.calculate_mean_visible(red, green, blue).astype(np.float64)
        whiteness = np.zeros_like(red).astype(np.float64)

        for band in bands:
            # whiteness += np.abs(np.divide((np.subtract(band, mean_visible)), mean_visible))
            whiteness += np.abs((band - mean_visible) / mean_visible)

        return whiteness, whiteness < 0.8

    def hot_test(self, blue: np.ndarray, red: np.ndarray) -> np.ndarray:
        """_summary_

        Args:
            b1 (np.ndarray): _description_
            b3 (np.ndarray): _description_

        Returns:
            np.ndarray: _description_
        """

        # Eq. 3
        # return np.multiply(np.subtract(b1, 0.5), np.subtract(b3, 0.08)) > 0
        red = 0.5 * red
        hot_test = blue - red - 0.08
        hot_test = hot_test > 0
        return hot_test

    def b4_over_b5_test(self, nir: np.ndarray, swir1: np.ndarray) -> np.ndarray:
        """_summary_

        Args:
            b4 (np.ndarray): _description_
            b5 (np.ndarray): _description_

        Returns:
            np.ndarray: _description_
        """

        # Eq. 4
        return np.divide(nir, swir1) > 0.75

    def pass_one(
        self,
        blue: np.ndarray,
        red: np.ndarray,
        nir: np.ndarray,
        swir1: np.ndarray,
        swir2: np.ndarray,
        bt: np.ndarray,
        ndvi: np.ndarray,
        ndsi: np.ndarray,
        whiteness_test: np.ndarray,
    ):
        # plt.figure()
        # plt.imshow(whiteness_test)
        # plt.show()

        # Eq. 6
        pcp = np.logical_and(self.basic_test(swir2, bt, ndvi, ndsi), whiteness_test)

        pcp = np.logical_and(pcp, self.hot_test(blue, red))
        pcp = np.logical_and(pcp, self.b4_over_b5_test(nir, swir1))

        return pcp

    def water_test(self, ndvi: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """_summary_

        Args:
            ndvi (np.ndarray): _description_
            b4 (np.ndarray): _description_

        Returns:
            np.ndarray: _description_
        """

        # plt.figure()
        # plt.imshow(
        #     np.logical_or(
        #         np.logical_and(ndvi < 0.01, nir < 0.11),
        #         np.logical_and(ndvi < 0.1, nir < 0.05),
        #     )
        # )
        # plt.axis("off")
        # plt.show()

        # Eq. 5
        return np.logical_or(
            np.logical_and(ndvi < 0.01, nir < 0.11),
            np.logical_and(ndvi < 0.1, nir < 0.05),
        )

    def clear_sky_water_test(self, water_test: np.array, b7: np.ndarray) -> np.ndarray:
        return np.logical_and(water_test, b7 < 0.03)

    def water_cloud_prob(
        self,
        water_test: np.ndarray,
        swir1: np.ndarray,
        swir2: np.ndarray,
        bt: np.ndarray,
    ) -> np.ndarray:
        """_summary_

        Args:
            water_test (np.ndarray): _description_
            b5 (np.ndarray): _description_
            b7 (np.ndarray): _description_
            bt (np.ndarray): _description_

        Returns:
            np.ndarray: _description_
        """

        # Eq. 7
        clear_sky_water = self.clear_sky_water_test(water_test=water_test, b7=swir2)

        # Eq. 8
        t_water = None
        try:
            t_water = np.percentile(bt[clear_sky_water], 82.5)
        except:
            t_water = np.zeros_like(bt)

        # Eq. 9
        w_temperature_prob = (t_water - bt) / 4

        # Eq. 10
        brightness_prob = np.minimum(swir1, 0.11) / 0.11

        # Eq. 11
        w_cloud_prob = w_temperature_prob * brightness_prob

        return w_cloud_prob

    def land_cloud_prob(
        self,
        bt: np.ndarray,
        modified_ndvi: np.ndarray,
        modified_ndsi: np.ndarray,
        whiteness: np.ndarray,
        clear_sky_land: list[np.ndarray],
    ):
        """_summary_

        Args:
            bt (np.ndarray): _description_
            modified_ndvi (np.ndarray): _description_
            modified_ndsi (np.ndarray): _description_
            whiteness (np.ndarray): _description_
            clear_sky_land (np.ndarray): _description_

        Returns:
            _type_: _description_
        """

        # Eq. 13
        try:
            t_low = np.percentile(bt[clear_sky_land], 17.5)
        except:
            t_low = 20

        try:
            t_high = np.percentile(bt[clear_sky_land], 82.5)
        except:
            t_high = 60

        # Eq. 14
        l_temperature_prob = (t_high + 4 - bt) / (t_high + 4 - (t_low - 4))

        # Eq. 15
        maximum = np.maximum(np.abs(modified_ndvi), np.abs(modified_ndsi))
        variability_prob = 1 - np.maximum(maximum, whiteness)
        # variability_prob = 1 - maximum
        # Eq. 16
        l_cloud_prob = l_temperature_prob * variability_prob

        return l_cloud_prob, t_low, t_high

    def pass_two(
        self,
        swir1: np.ndarray,
        swir2: np.ndarray,
        bt: np.ndarray,
        pcp: np.ndarray,
        modified_ndvi: np.ndarray,
        modified_ndsi: np.ndarray,
        water_test: np.ndarray,
        whiteness: np.ndarray,
    ) -> np.ndarray:
        """_summary_

        Args:
            b5 (np.ndarray): _description_
            b7 (np.ndarray): _description_
            bt (np.ndarray): _description_
            pcp (np.ndarray): _description_
            water_test (np.ndarray): _description_
            whiteness (np.ndarray): _description_

        Returns:
            np.ndarray: _description_
        """

        w_cloud_prob = self.water_cloud_prob(
            water_test=water_test, swir1=swir1, swir2=swir2, bt=bt
        )

        # plt.figure(figsize=(15, 15))
        # plt.imshow(w_cloud_prob > 0.2, cmap="rainbow")
        # plt.show()

        # Eq. 12
        clear_sky_land = np.logical_not(pcp) & np.logical_not(water_test)

        l_cloud_prob, t_low, t_high = self.land_cloud_prob(
            bt=bt,
            modified_ndvi=modified_ndvi,
            modified_ndsi=modified_ndsi,
            whiteness=whiteness,
            clear_sky_land=clear_sky_land,
        )

        # Eq. 17 Problem here
        try:
            land_threshold = np.percentile(l_cloud_prob[clear_sky_land], 82.5) + 0.2
        except:
            land_threshold = 0.5
        # land_threshold = np.percentile(l_cloud_prob[clear_sky_land], 10) #+ 0.2
        # land_threshold = np.percentile(l_cloud_prob[clear_sky_land], 92.5) + 0.2
        # land_threshold = np.percentile(l_cloud_prob[clear_sky_land], 42.5) + 0.2
        print("Land threshold: ", land_threshold)

        # Eq. 18
        # Clouds above water
        # pcl_1 = pcp & water_test & (w_cloud_prob > 0.5)
        pcl_1 = np.logical_and(pcp, water_test)
        pcl_1 = np.logical_and(pcl_1, w_cloud_prob > 0.5)

        # Clouds above land
        # pcl_2 = pcp & (water_test == False) & (l_cloud_prob > land_threshold)
        pcl_2 = np.logical_and(pcp, np.logical_not(water_test))
        pcl_2 = np.logical_and(pcl_2, l_cloud_prob > land_threshold)

        # plt.figure()
        # plt.subplot(1, 2, 1)
        # plt.imshow(l_cloud_prob > land_threshold)
        # plt.subplot(1, 2, 2)
        # plt.imshow(w_cloud_prob, cmap="rainbow")
        # plt.show()

        # High land cloud probability
        pcl_3 = np.logical_and(l_cloud_prob > 0.99, np.logical_not(water_test))
        # pcl_3 = (l_cloud_prob > 0.99) & (water_test == False)

        # temperature test
        pcl_4 = bt < (t_low - 35)

        # plt.figure()
        # plt.subplot(1, 2, 1)
        # plt.imshow(bt)
        # plt.show()

        # pcl =  np.logical_or(np.logical_or(np.logical_or(pcl_1, pcl_2), pcl_3), pcl_4)
        pcl = pcl_1 | pcl_2 | pcl_3 | pcl_4

        # plt.figure(figsize=(15, 15))
        # plt.imshow(pcl_1)
        # plt.show()

        # plt.figure(figsize=(15, 15))
        # plt.imshow(pcl_2)
        # plt.show()

        # plt.figure(figsize=(15, 15))
        # plt.imshow(pcl_3)
        # plt.show()

        # plt.figure(figsize=(15, 15))
        # plt.imshow(pcl_4)
        # plt.show()

        return pcl

    def detect_clouds(
        self,
        blue: np.ndarray,
        red: np.ndarray,
        nir: np.ndarray,
        swir1: np.ndarray,
        swir2: np.ndarray,
        bt: np.ndarray,
        ndvi: np.ndarray,
        ndsi: np.ndarray,
        modified_ndvi: np.ndarray,
        modified_ndsi: np.ndarray,
        whiteness_test: np.ndarray,
        whiteness: np.ndarray,
        water: np.ndarray,
    ) -> np.ndarray:
        # Pass One to get potencial cloud pixels
        pcp = self.pass_one(
            blue=blue,
            red=red,
            nir=nir,
            swir1=swir1,
            swir2=swir2,
            bt=bt,
            ndvi=ndvi,
            ndsi=ndsi,
            whiteness_test=whiteness_test,
        )

        # Pass Two returns potencial cloud layer
        # pcl = self.pass_two(
        #     swir1=swir1,
        #     swir2=swir1,
        #     bt=bt,
        #     pcp=pcp,
        #     modified_ndvi=modified_ndvi,
        #     modified_ndsi=modified_ndsi,
        #     water_test=water,
        #     whiteness=whiteness,
        # )

        return pcp

    def detect_shadows(self, nir: np.ndarray, water_test: np.ndarray):
        flood_fill_nir = calculate_flood_fill_transformation(nir)
        # PCSL(Potential Cloud Shadow Layer) test

        result = (
            ((flood_fill_nir - nir) > -0.1297589)
            & ((flood_fill_nir - nir) < -0.0249)
            & np.logical_not(water_test)
        )

        # plt.figure(figsize=(25, 15))
        # plt.imshow(result, cmap="gray")
        # plt.title("Flood fill")
        # plt.show()

        return result
        # return ((flood_fill_b4 - b4) < 25) & np.logical_not(water_test)

    def create_fmask(self, tif_file: str) -> np.ndarray:
        """Receives the landsat image and return the segmentation mask for
           cloud and cloud shadow

        Args:
            tif_file (str): Path to .tif with the bands

        Returns:
            np.ndarray: Mask containing cloud segmentation(value 1)
                        and cloud shadow (value 2)
        """
        # Open .tif
        bands = read_bands(tif_file)

        # # Extract each band landsat
        # B1 = bands[0]
        # B2 = bands[1]
        # B3 = bands[2]
        # B4 = bands[3]
        # B5 = bands[4]
        # B6 = bands[5]
        # B7 = bands[6]
        # saa_band = bands[9]
        # sza_band = bands[10]
        # vaa_band = bands[11]
        # vza_band = bands[12]

        # Extract each band sentinel
        B2 = bands[0] / self.scale_factor  # Blue
        B3 = bands[1] / self.scale_factor  # Green
        B4 = bands[2] / self.scale_factor  # Red
        B8 = bands[3] / self.scale_factor  # NIR
        B11 = bands[4] / self.scale_factor  # SWIR 1
        B12 = bands[5] / self.scale_factor  #

        # rgb = [B4/np.max(B4), B3/np.max(B3), B2/np.max(B2)]

        # rgb = np.transpose(np.stack(rgb), axes=[1, 2, 0])

        # plt.figure()
        # plt.imshow(rgb)
        # plt.show()

        # Calculate the necessary indices
        ndvi, modified_ndvi = calculate_ndvi(red=B4, nir=B8)
        ndwi = calculate_ndwi(green=B3, nir=B8)

        ndsi, modified_ndsi = calculate_ndsi(green=B3, swir1=B11)
        bt = B12 - 273.15
        whiteness, whiteness_test = self.whiteness_test(red=B4, green=B3, blue=B2)
        water_test = self.water_test(ndvi=ndvi, nir=B8)

        # Get cloud mask
        cloud_mask = self.detect_clouds(
            blue=B2,
            red=B4,
            nir=B8,
            swir1=B11,
            swir2=B12,
            bt=bt,
            ndvi=ndvi,
            ndsi=ndsi,
            modified_ndvi=modified_ndvi,
            modified_ndsi=modified_ndsi,
            whiteness=whiteness,
            whiteness_test=whiteness_test,
            water=water_test,
        )

        # plt.figure()
        # plt.imshow(cloud_mask)
        # plt.show()

        # Get shadow cloud mask
        shadow_mask = self.detect_shadows(nir=B8, water_test=water_test)

        # self.save_one_band_tif(shadow_mask, tif_file, 'shadow.tif')

        water_mask = np.logical_and(ndwi > 0.1, water_test)
        water_mask = Image.fromarray(water_mask).filter(ImageFilter.MaxFilter(size=3))
        # return ndwi, cloud_mask, shadow_mask
        return (
            np.transpose(np.array([bands[4], bands[3], bands[2]]), [1, 2, 0]),
            cloud_mask,
            shadow_mask,
            water_mask,
        )


if __name__ == "__main__":
    import os

    # root = './test_images'
    root = "./sentinel_scene/6B"

    inputs = [f"{root}/{img}" for img in os.listdir(root) if "TOA.tif" in img]
    # inputs = ['./2004/seixas_20041124.tif']
    # inputs = ['./2004/seixas_20040905.tif']

    save_dir = "./results/"

    # inputs = ['./Seixas_big_picture/TOA/2004/seixas_20040414.tif']
    # inputs = ['./Seixas/TOA/2004/seixas_20040905.tif']
    # inputs = ['seixas_20041124.tif']
    # save_dir = "./"

    fmask = Fmask()

    for inp in inputs:
        file_name = f'{inp.split("/")[-1].split(".")[0]}_result'

        color_composite, cloud_mask, shadow_mask, water_mask = fmask.create_fmask(inp)

        save_overlayed_mask_plot(
            [cloud_mask, shadow_mask, water_mask],
            color_composite,
            save_dir,
            name=file_name + ".png",
        )
        save_mask_tif(
            cloud_mask=cloud_mask,
            cloud_shadow_mask=shadow_mask,
            water_mask=water_mask,
            original_tif_file=inp,
            output_file=file_name + ".tif",
        )
