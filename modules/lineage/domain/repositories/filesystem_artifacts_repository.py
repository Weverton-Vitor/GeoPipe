import io
from pathlib import Path

import numpy as np
import rasterio
from domain.entities.image import ImageBOA
from domain.repositories.base import ArtifactRepository
from PIL import Image

from domain.entities.artifact import ArtifactImage


class FileSystemArtifactRepository(ArtifactRepository):
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)

        self.source_root_cloud_mask = self.base_path / "data" / "03_masks"
        self.source_root_cloud_free = self.base_path / "data" / "04_clean_images"
        self.source_root_water_mask = self.base_path / "data" / "07_water_mask"

        # onde vamos salvar os PNGs para o frontend
        self.output_root = self.base_path / "public" / "images"

    # ==========================
    # API pública do repository
    # ==========================
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
                    png_path = output_dir / source_dir_key / f"{tif_path.stem}_cloud_mask.png"
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
                else:
                    pass

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
        
    from pathlib import Path

    from PIL import Image


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

