import os
from datetime import datetime, timedelta, timezone

import ee
import requests
from tqdm import tqdm

from utils.fmask.fmask_utils import save_mask_tif, save_overlayed_mask_plot

CLOUD_FILTER = 60
CLD_PRB_THRESH = 50
NIR_DRK_THRESH = 0.15
CLD_PRJ_DIST = 1
BUFFER = 50


# ---------------------------------------------------------------------------
# Funções de máscara (sem alterações de lógica)
# ---------------------------------------------------------------------------


def get_s2_sr_cld_col(aoi_geom: ee.Geometry, start_date, end_date):
    """Retorna coleção S2 SR com s2cloudless joinado."""
    s2_sr_col = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(aoi_geom)
        .filterDate(start_date, end_date)
    )
    s2_cloudless_col = (
        ee.ImageCollection("COPERNICUS/S2_CLOUD_PROBABILITY")
        .filterBounds(aoi_geom)
        .filterDate(start_date, end_date)
    )
    print(f"Total de imagens S2 SR:        {s2_sr_col.size().getInfo()}")
    print(f"Total de imagens s2cloudless:  {s2_cloudless_col.size().getInfo()}")

    return ee.ImageCollection(
        ee.Join.saveFirst("s2cloudless").apply(
            primary=s2_sr_col,
            secondary=s2_cloudless_col,
            condition=ee.Filter.equals(
                leftField="system:index", rightField="system:index"
            ),
        )
    )


def add_cloud_bands(img):
    cld_prb = ee.Image(img.get("s2cloudless")).select("probability")
    is_cloud = cld_prb.gt(CLD_PRB_THRESH).rename("clouds")
    return img.addBands(ee.Image([cld_prb, is_cloud]))


def add_shadow_bands(img):
    not_water = img.select("SCL").neq(6)
    SR_BAND_SCALE = 1e4
    dark_pixels = (
        img.select("B8")
        .lt(NIR_DRK_THRESH * SR_BAND_SCALE)
        .multiply(not_water)
        .rename("dark_pixels")
    )
    shadow_azimuth = ee.Number(90).subtract(
        ee.Number(img.get("MEAN_SOLAR_AZIMUTH_ANGLE"))
    )
    cld_proj = (
        img.select("clouds")
        .directionalDistanceTransform(shadow_azimuth, CLD_PRJ_DIST * 10)
        # .reproject(crs=img.select(0).projection(), scale=10)
        .select("distance")
        .mask()
        .rename("cloud_transform")
    )
    shadows = cld_proj.multiply(dark_pixels).rename("shadows")
    return img.addBands(ee.Image([dark_pixels, cld_proj, shadows]))


def add_cld_shdw_mask(img):
    img_cloud = add_cloud_bands(img)
    img_cloud_shadow = add_shadow_bands(img_cloud)
    is_cld_shdw = (
        img_cloud_shadow.select("clouds").add(img_cloud_shadow.select("shadows")).gt(0)
    )
    is_cld_shdw = (
        is_cld_shdw.focalMin(2)
        # .focalMax(BUFFER * 2 / 20)
        # .reproject(crs=img.select([0]).projection(), scale=10)
        .rename("cloudmask")
    )
    return img_cloud_shadow.addBands(is_cld_shdw)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _next_day(date_str: str) -> str:
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return (d + timedelta(days=1)).strftime("%Y-%m-%d")


def _mosaic_by_date(
    collection: ee.ImageCollection,
    aoi_geom: ee.Geometry,
) -> list:
    """
    Agrupa imagens por data e faz mosaico recortado pela AOI.

    Retorna lista de dicts: [{"date": str, "image": ee.Image}, ...]

    Por que mosaico?
    ----------------
    O Sentinel-2 é distribuído por tiles de ~100 x 100 km. Se a AOI cruzar a
    fronteira entre dois tiles (ex.: 23KPQ e 23KPP), a mesma data terá duas
    imagens distintas. .mosaic() une os pixels das cenas do mesmo dia,
    eliminando lacunas na cobertura.
    """
    timestamps = collection.aggregate_array("system:time_start").getInfo()

    unique_dates = sorted(
        set(
            datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            for ts in timestamps
        )
    )

    mosaics = []
    for date_str in unique_dates:
        day_col = collection.filterDate(date_str, _next_day(date_str))
        n = day_col.size().getInfo()
        if n == 0:
            continue

        # mosaic() empilha as cenas (última data fica por cima);
        # clip() restringe o resultado à AOI — obrigatório antes do download.
        proj = day_col.first().select(0).projection()

        mosaic = (
            day_col.mosaic()#.reproject(proj)
            # .clip(aoi_geom)
        )
        mosaics.append({"date": date_str, "image": mosaic})
        # print(f"  [{date_str}] {n} cena(s) mosaicada(s)")

    return mosaics


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------
def export_s2_cloud_shadow_masks(
    roi_feature_collection: ee.featurecollection.FeatureCollection,
    location_name: str,
    start_date,
    end_date,
    output_dir,
    save_plots_path,
    generate_plots=False,
    scale: int = 10,
    cloud_filter: int = 60,
    cld_prb_thresh: int = 50,
    nir_drk_thresh: float = 0.15,
    cld_prj_dist: int = 1,
    buffer: int = 50,
):
    """
    Exporta localmente máscaras de nuvem/sombra Sentinel-2 via getDownloadURL().

    Parâmetros
    ----------
    roi_geometry    : ee.FeatureCollection | ee.Feature | ee.Geometry
    start_date      : str  – "YYYY-MM-DD"
    end_date        : str  – "YYYY-MM-DD"
    output_dir      : str  – pasta de saída (criada se não existir)
    scale           : int  – resolução em metros (padrão 10)
    crs             : str  – sistema de referência do GeoTIFF (padrão EPSG:4326)

    Bandas exportadas (GeoTIFF por data)
    ------------------------------------
    1. cloud_probability  – probabilidade s2cloudless (0-100)
    2. clouds             – pixels de nuvem (0/1)
    3. shadows            – pixels de sombra (0/1)
    4. cloud_shadow_mask  – máscara combinada e dilatada (0/1)
    """

    # Atualiza globals de threshold
    global CLOUD_FILTER, CLD_PRB_THRESH, NIR_DRK_THRESH, CLD_PRJ_DIST, BUFFER
    CLOUD_FILTER = cloud_filter
    CLD_PRB_THRESH = cld_prb_thresh
    NIR_DRK_THRESH = nir_drk_thresh
    CLD_PRJ_DIST = cld_prj_dist
    BUFFER = buffer

    # create all year in subfolder
    # for year in range(int(start_date.split("-")[0]), int(end_date.split("-")[0]) + 1):
    #     year_dir = os.path.join(output_dir, str(year))
    #     os.makedirs(year_dir, exist_ok=True)

    os.makedirs(output_dir, exist_ok=True)

    collection = get_s2_sr_cld_col(roi_feature_collection, start_date, end_date).map(
        add_cld_shdw_mask
    )

    n_total = collection.size().getInfo()
    print(f"\nTotal de imagens após processamento: {n_total}")
    if n_total == 0:
        print("Nenhuma imagem encontrada. Verifique AOI, datas e CLOUD_FILTER.")
        return

    # 4. Agrupa por data e mosaica
    print("\nAgrupando e mosaicando por data...")
    mosaics = _mosaic_by_date(collection, roi_feature_collection)
    print(f"\nTotal de datas únicas para exportar: {len(mosaics)}\n")

    # 5. Download por data
    for i, item in enumerate(
            tqdm(mosaics, desc="Downloading cloud/shadow masks", unit="imagem")
        ):
        date_str = item["date"]
        mosaic_img = item["image"]
        
        export_img = ee.Image.cat(
            [
                # mosaic_img.select("probability").rename("cloud_probability"),
                mosaic_img.select("clouds").rename("clouds").multiply(1).rename("clouds"),
                mosaic_img.select("shadows").rename("shadows").multiply(2).rename("shadows"),
                # mosaic_img.select("cloudmask").rename("cloud_shadow_mask"),
            ]
        ).toUint8()
        
        clouds = mosaic_img.select("clouds")
        shadows = mosaic_img.select("shadows")
        base_img = ee.Image.constant(0).uint8()

        # Aplica os valores na mesma banda (Sombra=2 tem prioridade sobre Nuvem=1 neste exemplo)
        final_band = base_img.where(clouds.eq(1), 1)\
                            .where(shadows.eq(1), 2)\
                            .rename("raster_class")

        export_img = final_band.toUint8()
        

        filename = os.path.join(
            output_dir, date_str.split("-")[0], f"S2_cloud_shadow_mask_{date_str}.tif"
        )

        if generate_plots:
            save_overlayed_mask_plot(
                [
                    mosaic_img.select("clouds").rename("clouds"),
                    mosaic_img.select("shadows"),
                ],
                mosaic_img.select(["B4", "B3", "B2"]),
                output_file=f"{save_plots_path}/{location_name}/{'s2cloudless'}/S2_cloud_shadow_mask_plot_{date_str}.png",
            )

        roi_bounds = roi_feature_collection.geometry().bounds()
        # print(roi_bounds.getInfo()["coordinates"])

        export_img = export_img.clip(roi_bounds)

        # region recebe o dict GeoJSON — nunca o objeto ee.Geometry
        url = export_img.getDownloadURL(
            {
                "scale": scale,
                "region": roi_bounds,
                "format": "GEO_TIFF",
            }
        )

        # print(f"Baixando {date_str} → {os.path.basename(filename)}")
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    print("\nDownload concluído.")
