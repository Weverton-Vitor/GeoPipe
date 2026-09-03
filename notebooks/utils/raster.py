import numpy as np
import rasterio

def calcular_classes_mascara(tif_path, nodata=None):
    """
    Calcula a quantidade e a porcentagem de pixels de cada classe da máscara.

    Parameters
    ----------
    tif_path : str
        Caminho para o arquivo TIFF.
    nodata : int ou float, optional
        Valor NoData. Se None, utiliza o valor definido no raster.

    Returns
    -------
    dict
        {
            classe: {
                "pixels": quantidade,
                "percentual": percentual
            },
            ...
        }
    """
    with rasterio.open(tif_path) as src:
        mask = src.read(1)


    classes, counts = np.unique(mask, return_counts=True)
    total = counts.sum()
    
    # print("mask.size:", mask.size)

    classes, counts = np.unique(mask, return_counts=True)
    # print("soma:", counts.sum())

    return {
        int(classe): {
            "pixels": int(count),
            "percentual": float(count / total * 100)
        }
        for classe, count in zip(classes, counts)
    }