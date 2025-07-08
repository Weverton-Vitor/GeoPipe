
import numpy as np
import rasterio
from rasterio.warp import Resampling, calculate_default_transform, reproject


def calculate_water_area(tif_path, binarization_gt=0):
    """
        Reprojeta uma imagem .tif com CRS geográfico (graus) para UTM (metros),
        e calcula a área de pixels de água (valor > 0).

        Parâmetros:
        - tif_path (str): caminho para o arquivo .tif

        Retorna:
        - Tuple: (area_m2, area_km2)
        """
    with rasterio.open(tif_path) as src:
        dst_crs = "EPSG:31984"  # SIRGAS 2000 / UTM zone 24S (Paraíba)

        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds)

        kwargs = src.meta.copy()
        kwargs.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height
        })

        with rasterio.MemoryFile() as memfile:
            with memfile.open(**kwargs) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=dst_crs,
                        resampling=Resampling.nearest
                    )

                image = dst.read(1)
                pixel_width = abs(dst.transform.a)
                pixel_height = abs(dst.transform.e)
                pixel_area = pixel_width * pixel_height

                water_pixels = np.sum(image > binarization_gt)
                water_area_m2 = water_pixels * pixel_area
                water_area_km2 = water_area_m2 / 1e6

                return water_area_m2, water_area_km2

