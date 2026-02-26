import io
import json
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from domain.entities.artifact import ArtifactImage
from domain.repositories.base import ArtifactRepository
from matplotlib import cm
from PIL import Image
from rasterio.features import rasterize
from rasterio.warp import transform_geom
from shapely.geometry import mapping, shape


class FileSystemArtifactRepository(ArtifactRepository):
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)

        self.source_root_shapefile = self.base_path / "data" / "00_shapefiles"
        self.source_root_cloud_mask = self.base_path / "data" / "03_masks"
        self.source_root_cloud_free = self.base_path / "data" / "04_clean_images"
        self.source_root_water_mask = self.base_path / "data" / "07_water_masks"

        # onde vamos salvar os PNGs para o frontend
        self.output_root = self.base_path / "public" / "images"

    # ==========================
    # API pública do repository
    # ==========================
    def get_binary_artifact(self, run: str, year: str, month: str, day: str, threshold):
        """
        Retorna o conteúdo binário do artefato (ex: imagem TIFF) para download
        """
        source_dirs = self._get_source_dirs(run, year)
        output_dir = self._get_output_dir(run, year, month)

        if not any(source_dirs.values()):
            return []

        tif_paths = list(source_dirs["water_mask"].glob("*.tif"))
        if not tif_paths:
            return []

        tif_path = tif_paths[0]

        png_path = (
            output_dir / "water_mask" / f"{tif_path.stem}_water_mask_{threshold}.png"
        )

        (output_dir / "water_mask").mkdir(parents=True, exist_ok=True)

        if not png_path.exists():
            self._generate_binary_mask_image(tif_path, png_path, threshold=threshold)

        path = f"/static/images/{run}/{year}/{month}/artifacts/water_mask/{Path(png_path).name}"

        return ArtifactImage(
            name=tif_path.name,
            path=path,
            image_type="water_mask",
        )

    def get_artifacts(
        self, run: str, year: str, month: str, day: str = ""
    ) -> list[ArtifactImage]:
        source_dirs = self._get_source_dirs(run, year)
        output_dir = self._get_output_dir(run, year, month)

        if not any(source_dirs.values()):
            return []

        artifacs: list[ArtifactImage] = []

        for source_dir_key in source_dirs.keys():
            (output_dir / source_dir_key).mkdir(parents=True, exist_ok=True)
            for tif_path in source_dirs[source_dir_key].glob("*.tif"):
                if not self._matches_date(tif_path.name, year, month, day):
                    continue

                if source_dir_key == "clean":
                    png_path = output_dir / source_dir_key / f"{tif_path.stem}.png"
                    if not png_path.exists():
                        self._convert_tif_to_png(tif_path, png_path)

                    path = f"/static/images/{run}/{year}/{month}/artifacts/{source_dir_key}/{Path(png_path).name}"

                    artifacs.append(
                        ArtifactImage(
                            name=tif_path.name,
                            path=path,
                            image_type=source_dir_key,
                        )
                    )
                elif source_dir_key == "cloud_mask":
                    png_path = (
                        output_dir / source_dir_key / f"{tif_path.stem}_cloud_mask.png"
                    )
                    if not png_path.exists():
                        self._generate_fmask_overlay_image(tif_path, png_path)
                    path = f"/static/images/{run}/{year}/{month}/artifacts/{source_dir_key}/{Path(png_path).name}"

                    artifacs.append(
                        ArtifactImage(
                            name=tif_path.name,
                            path=path,
                            image_type=source_dir_key,
                        )
                    )
                elif source_dir_key == "water_mask":
                    (output_dir / source_dir_key / "probs").mkdir(
                        parents=True, exist_ok=True
                    )

                    png_path = (
                        output_dir
                        / source_dir_key
                        / "probs"
                        / f"{tif_path.stem}_water_probabilities.png"
                    )

                    if not png_path.exists():
                        self._generate_probability_image(tif_path, png_path)
                    path = f"/static/images/{run}/{year}/{month}/artifacts/{source_dir_key}/probs/{Path(png_path).name}"

                    artifacs.append(
                        ArtifactImage(
                            name=tif_path.name,
                            path=path,
                            image_type=source_dir_key,
                        )
                    )

            if source_dir_key == "shapefile":
                tif_path = list(source_dirs["clean"].glob("*.tif"))[0]
                (self.output_root / run / source_dir_key).mkdir(parents=True, exist_ok=True)

                png_path = (
                    self.output_root / run / source_dir_key / f"{tif_path.stem}_shapefile.png"
                )
                
                print(png_path)
                
                shapefile = [
                    file
                    for file in os.listdir(self.source_root_shapefile)
                    if file.split(".")[0] in tif_path.stem and file.endswith(".geojson")
                ]

                tif_path_shapefile = self.source_root_shapefile / shapefile[0]

                if not png_path.exists():
                    self.generate_geojson_outline_png(
                        reference_raster_path=tif_path,
                        geojson_path=tif_path_shapefile,
                        output_png_path=png_path,
                    )

                path = f"/static/images/{run}/{source_dir_key}/{Path(png_path).name}"

                artifacs.append(
                    ArtifactImage(
                        name=tif_path.name,
                        path=path,
                        image_type=source_dir_key,
                    )
                )

        return artifacs

    # ==========================
    # Funções auxiliares
    # ==========================
    def _get_source_dirs(self, run: str, year: str) -> Path:
        """
        data/02_boa_images/<run>/<year>
        """

        paths = {
            "cloud_mask": self.source_root_cloud_mask / run / year,
            "clean": self.source_root_cloud_free / run / year,
            "water_mask": self.source_root_water_mask / run / year,
            "shapefile": self.source_root_shapefile,
        }

        return paths

    def _get_output_dir(self, run: str, year: str, month: str) -> Path:
        """
        public/images/<run>/<year>/<month>
        """
        return self.output_root / run / year / month / "artifacts"

    def _matches_date(
        self, filename: str, year: str, month: str, day: str = ""
    ) -> bool:
        """
        Verifica se o nome do arquivo contém YYYYMM
        """
        if day:
            return f"{year}{month}{day}" in filename

        return f"{year}{month}" in filename

    def _convert_tif_to_png(self, tif_path: Path, png_path: Path):
        """
        Converte Sentinel TIFF multibanda para PNG RGB (visualização)
        """
        with rasterio.open(tif_path) as src:
            # Sentinel-2 padrão: B4=Red, B3=Green, B2=Blue
            red = src.read(3)
            green = src.read(2)
            blue = src.read(1)

        rgb = np.dstack((red, green, blue))

        # normalização simples para visualização
        rgb_norm = np.clip(rgb / 3000 * 255, 0, 255).astype(np.uint8)

        img = Image.fromarray(rgb_norm)
        img.save(png_path, format="PNG")

    def _generate_fmask_overlay_image(self, input_tif: Path, output_png: Path):
        with rasterio.open(input_tif) as src:
            mask = src.read(1)

        height, width = mask.shape

        # cria imagem RGBA vazia
        rgba = np.zeros((height, width, 4), dtype=np.uint8)

        # classe 1 = nuvem (branco semi-transparente)
        cloud = mask == 1
        rgba[cloud] = [255, 255, 0, 150]

        # classe 2 = sombra (azul escuro semi-transparente)
        shadow = mask == 2
        rgba[shadow] = [180, 0, 0, 150]

        # fundo já está [0,0,0,0] (transparente)

        img = Image.fromarray(rgba, mode="RGBA")
        img.save(output_png)

    def _generate_probability_image(self, input_tif: Path, output_png: Path):
        with rasterio.open(input_tif) as src:
            prob = src.read(1).astype(np.float32)

        if prob.max() > 1:
            prob = prob / 100.0

        prob = np.clip(prob, 0, 1)

        from matplotlib import cm

        colormap = cm.get_cmap("viridis")
        colored = colormap(prob)

        rgba = (colored * 255).astype(np.uint8)

        rgba[..., 3] = 140

        img = Image.fromarray(rgba, mode="RGBA")
        img.save(output_png)

    def _generate_binary_mask_image(
        self, input_tif: Path, output_png: Path, threshold: float = 0.5
    ):
        with rasterio.open(input_tif) as src:
            prob = src.read(1).astype(np.float32)

        if prob.max() > 1:
            prob = prob / 100.0

        mask = prob >= threshold

        height, width = mask.shape
        rgba = np.zeros((height, width, 4), dtype=np.uint8)

        # azul água semi-transparente
        rgba[mask] = [0, 150, 255, 180]

        img = Image.fromarray(rgba, mode="RGBA")
        img.save(output_png)

    def generate_geojson_outline_png(
        self,
        geojson_path,
        reference_raster_path,
        output_png_path,
        line_color=(255, 255, 0, 255),  # amarelo sólido
    ):
        """
        Gera PNG transparente com apenas o contorno do GeoJSON,
        alinhado ao raster de referência.
        """
        

        # 🔹 1️⃣ Abrir raster de referência
        with rasterio.open(reference_raster_path) as src:
            transform = src.transform
            crs = src.crs
            width = src.width
            height = src.height

        # 🔹 2️⃣ Ler GeoJSON
        with open(geojson_path) as f:
            geojson = json.load(f)

        shapes = []

        for feature in geojson["features"]:
            geom = feature["geometry"]

            # 🔹 3️⃣ Reprojetar para CRS do raster se necessário
            if geojson.get("crs"):
                geom = transform_geom(geojson["crs"]["properties"]["name"], crs, geom)

            # converter para shapely
            shp = shape(geom)

            # pegar apenas contorno (boundary)
            boundary = shp.boundary

            shapes.append((mapping(boundary), 1))

        # 🔹 4️⃣ Rasterizar contorno
        mask = rasterize(
            shapes=shapes,
            out_shape=(height, width),
            transform=transform,
            fill=0,
            dtype="uint8",
            all_touched=True,
        )

        # 🔹 5️⃣ Criar imagem RGBA transparente
        rgba = np.zeros((height, width, 4), dtype=np.uint8)

        # aplicar cor somente onde mask == 1
        rgba[mask == 1] = line_color

        # 🔹 6️⃣ Salvar PNG
        img = Image.fromarray(rgba, mode="RGBA")
        img.save(output_png_path)
