"""
Landsat Time-Series Downloader via Google Earth Engine
=======================================================
Baixa imagens de toda a série histórica Landsat (5 → 9) para uma ROI
definida por um arquivo GeoJSON. Suporta mosaico multi-path/row,
crop por bounding box e divisão em patches remontáveis.

Uso:
    python landsat_gee_downloader.py \
        --geojson minha_area.geojson \
        --output_dir ./landsat_download \
        --start_year 1984 \
        --end_year 2024 \
        --cloud_cover 30 \
        --patch_size 1024
"""

import ee
import geojson
import json
import os
import math
import time
import argparse
import logging
import requests
from pathlib import Path
from datetime import datetime, date
from typing import Any

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuração das coleções Landsat
# ---------------------------------------------------------------------------
LANDSAT_COLLECTIONS = [
    # (satélite, coleção SR, bandas originais → bandas normalizadas, início, fim)
    {
        "name": "Landsat5",
        "collection": "LANDSAT/LT05/C02/T1_L2",
        "bands": ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B7", "QA_PIXEL"],
        "band_names": ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2", "CFmask"],
        "start": "1984-01-01",
        "end": "2013-06-05",
        "scale": 0.0000275,
        "offset": -0.2,
    },
    {
        "name": "Landsat7",
        "collection": "LANDSAT/LE07/C02/T1_L2",
        "bands": ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B7", "QA_PIXEL"],
        "band_names": ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2", "CFmask"],
        "start": "1999-01-01",
        "end": "2024-12-31",
        "scale": 0.0000275,
        "offset": -0.2,
    },
    {
        "name": "Landsat8",
        "collection": "LANDSAT/LC08/C02/T1_L2",
        "bands": ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7", "QA_PIXEL"],
        "band_names": ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2", "CFmask"],
        "start": "2013-01-01",
        "end": "2024-12-31",
        "scale": 0.0000275,
        "offset": -0.2,
    },
    {
        "name": "Landsat9",
        "collection": "LANDSAT/LC09/C02/T1_L2",
        "bands": ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7", "QA_PIXEL"],
        "band_names": ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2", "CFmask"],
        "start": "2021-10-31",
        "end": "2024-12-31",
        "scale": 0.0000275,
        "offset": -0.2,
    },
]

# Preferência de satélite para cada período (evita sobreposição duplicada)
# L5 → L7 (quando L5 falhou) → L8 → L9
PRIORITY_WINDOWS = [
    ("1984-01-01", "1999-04-14", ["Landsat5"]),
    ("1999-04-15", "2003-05-30", ["Landsat7", "Landsat5"]),
    ("2003-05-31", "2013-01-01", ["Landsat5", "Landsat7"]),  # L7 scan-line error
    ("2013-01-01", "2021-10-30", ["Landsat8", "Landsat7"]),
    ("2021-10-31", "2099-12-31", ["Landsat9", "Landsat8"]),
]


# ---------------------------------------------------------------------------
# Autenticação GEE
# ---------------------------------------------------------------------------
def authenticate_gee(project: str | None = None):
    """Autentica no GEE. Tenta service account via variável de ambiente primeiro."""
    try:
        if project:
            ee.Initialize(project=project)
        else:
            ee.Initialize()
        log.info("GEE inicializado com sucesso.")
    except Exception:
        log.info("Rodando autenticação interativa do GEE...")
        ee.Authenticate()
        if project:
            ee.Initialize(project=project)
        else:
            ee.Initialize()
        log.info("GEE autenticado e inicializado.")


# ---------------------------------------------------------------------------
# Leitura e conversão do GeoJSON
# ---------------------------------------------------------------------------
def load_geojson(path: str) -> dict:
    with open(path) as f:
        gj = json.load(f)
    return gj


def geojson_to_ee_geometry(gj: dict) -> ee.Geometry:
    """Converte um GeoJSON (Feature, FeatureCollection ou Geometry) em ee.Geometry.

    Filtra automaticamente features com geometrias degeneradas (polígonos com
    todos os vértices iguais, anéis com menos de 3 pontos distintos, etc.)
    que causariam erros silenciosos no GEE.
    """
    def is_valid_polygon(coords: list) -> bool:
        """Verifica se o anel exterior tem pelo menos 3 pontos distintos."""
        if not coords or not coords[0]:
            return False
        outer_ring = coords[0]
        distinct = {(round(p[0], 8), round(p[1], 8)) for p in outer_ring}
        return len(distinct) >= 3

    if gj["type"] == "FeatureCollection":
        valid_features = []
        for feat in gj["features"]:
            geom = feat.get("geometry", {})
            geom_type = geom.get("type", "")
            coords = geom.get("coordinates", [])

            if geom_type == "Polygon" and not is_valid_polygon(coords):
                log.warning(
                    "Feature com polígono degenerado ignorada "
                    f"(vértices insuficientes ou todos iguais): {coords[:2]}..."
                )
                continue
            valid_features.append(feat)

        if not valid_features:
            raise ValueError("Nenhuma feature válida encontrada no FeatureCollection.")

        if len(valid_features) == 1:
            return ee.Geometry(valid_features[0]["geometry"])

        # Monta um FeatureCollection limpo e extrai a geometria unida
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry(f["geometry"])) for f in valid_features])
        return fc.geometry()

    elif gj["type"] == "Feature":
        return ee.Geometry(gj["geometry"])
    else:
        return ee.Geometry(gj)


def get_bounding_box(geometry: ee.Geometry) -> ee.Geometry:
    """Retorna o bounding box retangular da geometria."""
    return geometry.bounds()


def get_bbox_coords(geometry: ee.Geometry) -> tuple[float, float, float, float]:
    """Retorna (lon_min, lat_min, lon_max, lat_max) do bbox."""
    coords = geometry.bounds().coordinates().getInfo()[0]
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return min(lons), min(lats), max(lons), max(lats)


# ---------------------------------------------------------------------------
# Máscara de nuvem
# ---------------------------------------------------------------------------
def mask_clouds_landsat_c2(image: ee.Image) -> ee.Image:
    """Máscara baseada na banda QA_PIXEL do Landsat Collection 2."""
    qa = image.select("QA_PIXEL")
    # Bit 3: Cloud, Bit 4: Cloud Shadow, Bit 1: Dilated Cloud
    cloud_mask = (
        qa.bitwiseAnd(1 << 3).eq(0)
        .And(qa.bitwiseAnd(1 << 4).eq(0))
        .And(qa.bitwiseAnd(1 << 1).eq(0))
    )
    return image.updateMask(cloud_mask)


# ---------------------------------------------------------------------------
# Normalização de bandas (aplica escala e offset do SR)
# ---------------------------------------------------------------------------
def apply_scale_factors(image: ee.Image, scale: float, offset: float) -> ee.Image:
    optical = image.select("SR_B.*").multiply(scale).add(offset)
    return image.addBands(optical, overwrite=True)


# ---------------------------------------------------------------------------
# Construção da coleção por satélite
# ---------------------------------------------------------------------------
def build_collection(
    sat_cfg: dict,
    roi: ee.Geometry,
    date_start: str,
    date_end: str,
    cloud_cover: int,
) -> ee.ImageCollection:
    sat_name = sat_cfg["name"]  # captura o valor agora, evita closure em loop

    def prepare(img: ee.Image) -> ee.Image:
        img = mask_clouds_landsat_c2(img)
        img = apply_scale_factors(img, sat_cfg["scale"], sat_cfg["offset"])
        img = img.select(sat_cfg["bands"], sat_cfg["band_names"])
        # Seta date_str e satellite aqui mesmo, garantindo que fiquem no objeto
        date_str = img.date().format("YYYY-MM-dd")
        return img.set("date_str", date_str, "satellite", sat_name)

    col = (
        ee.ImageCollection(sat_cfg["collection"])
        .filterBounds(roi)
        .filterDate(date_start, date_end)
        .filter(ee.Filter.lt("CLOUD_COVER", cloud_cover))
        .map(prepare)
    )
    print(col.size().getInfo(), "imagens encontradas para", sat_name)
    return col


# ---------------------------------------------------------------------------
# Mosaico por data / cena
# ---------------------------------------------------------------------------
def mosaic_by_date1(collection: ee.ImageCollection, roi: ee.Geometry) -> list[dict]:
    """
    Agrupa imagens pela data de aquisição (YYYY-MM-DD) e cria um mosaico
    mediano para cada data. Retorna lista de dicts {date, image}.
    """
    # Pega datas únicas
    dates = (
        collection
        .map(lambda img: img.set("date_str", img.date().format("YYYY-MM-dd")))
        .aggregate_array("date_str")
        .distinct()
        .sort()
    )
    dates_list: list[str] = dates.getInfo()
    log.info(f"  Datas únicas encontradas: {len(dates_list)}")

    scenes = []
    for date_str in dates_list:
        day_col = collection.filter(
            ee.Filter.eq("date_str", date_str)  # type: ignore
        )
        # Usa median para suavizar artefatos de sobreposição entre paths/rows
        mosaic = day_col.median().clip(roi)
        mosaic = mosaic.set("date_str", date_str)
        scenes.append({"date": date_str, "image": mosaic})

    return scenes


from datetime import datetime, timedelta


def mosaic_by(
    collection: ee.ImageCollection,
    roi: ee.Geometry,
    window_days: int = 10
) -> list[dict]:
    """
    Agrupa imagens Landsat por janela temporal.

    Exemplo:
        Se window_days=2:
        imagens entre 01 e 03 serão mosaificadas juntas.
    """

    # Adiciona string de data
    collection = collection.map(
        lambda img: img.set(
            "date_str",
            img.date().format("YYYY-MM-dd")
        )
    )

    # Datas únicas
    dates = (
        collection
        .aggregate_array("date_str")
        .distinct()
        .sort()
    )

    dates_list = dates.getInfo()

    parsed_dates = sorted([
        datetime.strptime(d, "%Y-%m-%d")
        for d in dates_list
    ])

    groups = []
    used = set()

    for date in parsed_dates:

        if date in used:
            continue

        start = date
        end = date + timedelta(days=window_days)

        group = [
            d for d in parsed_dates
            if start <= d <= end
        ]

        for d in group:
            used.add(d)

        groups.append(group)

    scenes = []

    for group in groups:

        start_date = group[0].strftime("%Y-%m-%d")
        end_date = (group[-1] + timedelta(days=1)).strftime("%Y-%m-%d")

        group_col = collection.filterDate(
            start_date,
            end_date
        )

        mosaic = (
            group_col
            .median()
            .clip(roi)
            .set("start_date", start_date)
            .set("end_date", group[-1].strftime("%Y-%m-%d"))
        )

        scenes.append({
            "start_date": start_date,
            "end_date": group[-1].strftime("%Y-%m-%d"),
            "image": mosaic
        })

    return scenes

# ---------------------------------------------------------------------------
# Divisão em patches
# ---------------------------------------------------------------------------
def compute_patches(
    lon_min: float,
    lat_min: float,
    lon_max: float,
    lat_max: float,
    patch_size_px: int,
    scale_m: float,
) -> list[dict]:
    """
    Divide o bounding box em patches de patch_size_px × patch_size_px pixels.
    Retorna lista de dicts com metadados de cada patch para remontagem.

    Parâmetros:
        lon_min, lat_min, lon_max, lat_max – coordenadas geográficas do bbox
        patch_size_px – tamanho do patch em pixels (lado)
        scale_m – resolução espacial em metros/pixel (ex: 30 para Landsat)

    Retorna lista de dicts:
        {
            "row": int,       # índice de linha (y) começando de 0 (norte → sul)
            "col": int,       # índice de coluna (x) começando de 0 (oeste → leste)
            "lon_min": float, # limites do patch
            "lat_min": float,
            "lon_max": float,
            "lat_max": float,
            "width_px": int,  # largura real (pode ser menor na borda direita)
            "height_px": int, # altura real (pode ser menor na borda inferior)
        }
    """
    # Estima tamanho total em graus
    lon_extent = lon_max - lon_min
    lat_extent = lat_max - lat_min

    # Converte patch_size de pixels para graus (aproximação)
    # 1 grau lat ≈ 111_000 m; 1 grau lon ≈ 111_000 * cos(lat) m
    lat_center = (lat_min + lat_max) / 2
    meters_per_deg_lat = 111_000.0
    meters_per_deg_lon = 111_000.0 * math.cos(math.radians(lat_center))

    patch_deg_lat = (patch_size_px * scale_m) / meters_per_deg_lat
    patch_deg_lon = (patch_size_px * scale_m) / meters_per_deg_lon

    n_rows = math.ceil(lat_extent / patch_deg_lat)
    n_cols = math.ceil(lon_extent / patch_deg_lon)

    patches = []
    for row in range(n_rows):
        for col in range(n_cols):
            p_lon_min = lon_min + col * patch_deg_lon
            p_lat_max = lat_max - row * patch_deg_lat  # lat decresce de cima p/ baixo
            p_lon_max = min(p_lon_min + patch_deg_lon, lon_max)
            p_lat_min = max(p_lat_max - patch_deg_lat, lat_min)

            # Largura/altura real em pixels desta célula
            w_deg = p_lon_max - p_lon_min
            h_deg = p_lat_max - p_lat_min
            w_px = round(w_deg / patch_deg_lon * patch_size_px)
            h_px = round(h_deg / patch_deg_lat * patch_size_px)

            patches.append(
                {
                    "row": row,
                    "col": col,
                    "total_rows": n_rows,
                    "total_cols": n_cols,
                    "lon_min": p_lon_min,
                    "lat_min": p_lat_min,
                    "lon_max": p_lon_max,
                    "lat_max": p_lat_max,
                    "width_px": max(w_px, 1),
                    "height_px": max(h_px, 1),
                }
            )

    log.info(
        f"  Grade de patches: {n_rows} linhas × {n_cols} colunas = {len(patches)} patches"
    )
    return patches


# ---------------------------------------------------------------------------
# Download de um patch
# ---------------------------------------------------------------------------
def download_patch(
    image: ee.Image,
    patch: dict,
    output_path: Path,
    scale: float,
    bands: list[str],
    max_retries: int = 5,
) -> bool:
    """
    Baixa um patch via getDownloadURL e salva em output_path (GeoTIFF).
    Retorna True se bem-sucedido.
    """
    region = ee.Geometry.Rectangle(
        [patch["lon_min"], patch["lat_min"], patch["lon_max"], patch["lat_max"]]
    )

    params = {
        "scale": scale,
        "region": region,
        "format": "GEO_TIFF",
        "bands": bands,
        "crs": "EPSG:4326",
    }

    for attempt in range(1, max_retries + 1):
        try:
            url = image.getDownloadURL(params)
            resp = requests.get(url, timeout=600)
            resp.raise_for_status()
            output_path.write_bytes(resp.content)
            return True
        except Exception as exc:
            wait = 2 ** attempt
            log.warning(
                f"    Tentativa {attempt}/{max_retries} falhou: {exc}. "
                f"Aguardando {wait}s..."
            )
            time.sleep(wait)

    log.error(f"    Falha definitiva ao baixar {output_path.name}")
    return False


# ---------------------------------------------------------------------------
# Salva metadados da cena (para remontagem)
# ---------------------------------------------------------------------------
def save_scene_metadata(scene_dir: Path, date_str: str, satellite: str, patches: list[dict], bands: list[str], scale: float):
    meta = {
        "date": date_str,
        "satellite": satellite,
        "scale_m": scale,
        "crs": "EPSG:4326",
        "bands": bands,
        "total_rows": patches[0]["total_rows"],
        "total_cols": patches[0]["total_cols"],
        "patches": [
            {
                "filename": f"patch_r{p['row']:04d}_c{p['col']:04d}.tif",
                "row": p["row"],
                "col": p["col"],
                "lon_min": p["lon_min"],
                "lat_min": p["lat_min"],
                "lon_max": p["lon_max"],
                "lat_max": p["lat_max"],
                "width_px": p["width_px"],
                "height_px": p["height_px"],
            }
            for p in patches
        ],
    }
    meta_path = scene_dir / "scene_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    log.info(f"  Metadados salvos em {meta_path}")


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------
def run_download(
    geojson_path: str,
    output_dir: str,
    start_year: int,
    end_year: int,
    cloud_cover: int,
    patch_size_px: int,
    scale_m: float,
    gee_project: str | None,
    satellites: list[str] | None,
):
    # 1. Autenticação
    authenticate_gee(gee_project)

    # 2. Carrega ROI
    gj = load_geojson(geojson_path)
    roi_geom = geojson_to_ee_geometry(gj)
    bbox_geom = get_bounding_box(roi_geom)
    lon_min, lat_min, lon_max, lat_max = get_bbox_coords(roi_geom)
    log.info(
        f"ROI bbox: lon=[{lon_min:.4f}, {lon_max:.4f}], lat=[{lat_min:.4f}, {lat_max:.4f}]"
    )

    # 3. Grade de patches (fixa para toda a série → garante remontagem coerente)
    patches = compute_patches(lon_min, lat_min, lon_max, lat_max, patch_size_px, scale_m)

    # 4. Itera sobre os satélites configurados
    date_start = f"{start_year}-01-01"
    date_end = f"{end_year}-12-31"

    all_collections = []
    sat_filter = set(satellites) if satellites else None

    for sat_cfg in LANDSAT_COLLECTIONS:
        if sat_filter and sat_cfg["name"] not in sat_filter:
            continue
        # Restringe ao intervalo disponível do satélite
        s = max(date_start, sat_cfg["start"])
        e = min(date_end, sat_cfg["end"])
        if s >= e:
            continue
        log.info(f"Carregando {sat_cfg['name']} ({s} → {e})...")
        col = build_collection(sat_cfg, bbox_geom, s, e, cloud_cover)
        # date_str e satellite já são setados dentro de build_collection
        all_collections.append((sat_cfg, col))

    if not all_collections:
        log.error("Nenhuma coleção encontrada para os parâmetros fornecidos.")
        return

    # 5. Une todas as coleções e agrupa por data
    log.info("Unindo coleções e agrupando por data...")

    # Junta todas as coleções num único ImageCollection
    merged = all_collections[0][1]
    for _, col in all_collections[1:]:
        merged = merged.merge(col)

    # Pega datas únicas
    dates_list: list[str] = (
        merged.aggregate_array("date_str").distinct().sort().getInfo()
    )
    log.info(f"Total de cenas únicas: {len(dates_list)}")

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    # 6. Itera por data (cena)
    for date_str in dates_list:
        log.info(f"\n{'='*60}")
        log.info(f"Processando cena: {date_str}")

        # Filtra imagens dessa data
        day_col = merged.filter(ee.Filter.eq("date_str", date_str))

        # Descobre qual satélite predomina nesse dia
        sats_in_day: list[str] = day_col.aggregate_array("satellite").distinct().getInfo()
        satellite_label = "_".join(sorted(sats_in_day))

        # Mosaico mediano (une paths/rows diferentes)
        mosaic = day_col.median().clip(bbox_geom)

        # Descobre as bandas disponíveis (usa a configuração do primeiro satélite do dia)
        band_names = ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2"]
        # Seleciona apenas as bandas disponíveis na imagem mosaicada
        try:
            available = mosaic.bandNames().getInfo()
            bands_to_use = [b for b in band_names if b in available]
        except Exception:
            bands_to_use = band_names

        if not bands_to_use:
            log.warning(f"  Nenhuma banda válida encontrada para {date_str}. Pulando.")
            continue

        # 7. Cria diretório da cena: output_dir/<YYYY-MM-DD>_<satelite>/
        scene_dir_name = f"{date_str}_{satellite_label}"
        scene_dir = output_root / scene_dir_name
        scene_dir.mkdir(parents=True, exist_ok=True)

        # 8. Salva metadados da cena
        save_scene_metadata(scene_dir, date_str, satellite_label, patches, bands_to_use, scale_m)

        # 9. Baixa cada patch
        total_patches = len(patches)
        success_count = 0
        skip_count = 0

        for i, patch in enumerate(patches):
            patch_filename = f"patch_r{patch['row']:04d}_c{patch['col']:04d}.tif"
            patch_path = scene_dir / patch_filename

            if patch_path.exists():
                log.info(f"  [{i+1}/{total_patches}] {patch_filename} já existe. Pulando.")
                skip_count += 1
                continue

            log.info(
                f"  [{i+1}/{total_patches}] Baixando {patch_filename} "
                f"(row={patch['row']}, col={patch['col']}, "
                f"{patch['width_px']}×{patch['height_px']}px)..."
            )

            ok = download_patch(
                image=mosaic.select(bands_to_use),
                patch=patch,
                output_path=patch_path,
                scale=scale_m,
                bands=bands_to_use,
            )

            if ok:
                success_count += 1
                log.info(f"    ✓ {patch_filename} salvo ({patch_path.stat().st_size // 1024} KB)")
            else:
                log.error(f"    ✗ Falha em {patch_filename}")

            # Pequena pausa para não sobrecarregar a API
            time.sleep(0.5)

        log.info(
            f"  Cena {date_str}: {success_count} baixados, "
            f"{skip_count} pulados (já existiam), "
            f"{total_patches - success_count - skip_count} falhas"
        )

    log.info("\n" + "="*60)
    log.info("Download concluído!")
    log.info(f"Arquivos salvos em: {output_root.resolve()}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Baixa séries temporais Landsat (5-9) via GEE para uma ROI GeoJSON."
    )
    parser.add_argument(
        "--geojson", required=True,
        help="Caminho para o arquivo GeoJSON da área de interesse."
    )
    parser.add_argument(
        "--output_dir", default="./landsat_output",
        help="Diretório raiz onde as cenas serão salvas. (default: ./landsat_output)"
    )
    parser.add_argument(
        "--start_year", type=int, default=1984,
        help="Ano de início (default: 1984 – lançamento do Landsat 5)."
    )
    parser.add_argument(
        "--end_year", type=int, default=datetime.now().year,
        help="Ano de fim (default: ano atual)."
    )
    parser.add_argument(
        "--cloud_cover", type=int, default=30,
        help="Cobertura máxima de nuvens em %% (default: 30)."
    )
    parser.add_argument(
        "--patch_size", type=int, default=512,
        help="Tamanho do patch em pixels (default: 512). Recomendado: 256-1024."
    )
    parser.add_argument(
        "--scale", type=float, default=30.0,
        help="Resolução espacial em metros/pixel (default: 30 para Landsat)."
    )
    parser.add_argument(
        "--project", default=None,
        help="ID do projeto GEE (ex: my-gee-project). Opcional."
    )
    parser.add_argument(
        "--satellites", nargs="+",
        choices=["Landsat5", "Landsat7", "Landsat8", "Landsat9"],
        default=None,
        help="Satélites a incluir (default: todos). Ex: --satellites Landsat8 Landsat9"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_download(
        geojson_path=args.geojson,
        output_dir=args.output_dir,
        start_year=args.start_year,
        end_year=args.end_year,
        cloud_cover=args.cloud_cover,
        patch_size_px=args.patch_size,
        scale_m=args.scale,
        gee_project=args.project,
        satellites=args.satellites,
    )