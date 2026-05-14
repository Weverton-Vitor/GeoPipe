import io
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image

from domain.entities.image import ImageBOA
from domain.repositories.base import ImageRepository

class FileSystemImageRepository(ImageRepository):
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)

        # onde estão os TIFFs do pipeline
        self.source_root = self.base_path / "data" / "02_boa_images"

        # onde vamos salvar os PNGs para o frontend
        self.output_root = self.base_path / "public" / "images"

    # ==========================
    # API pública do repository
    # ==========================
    def get_images(self, run: str, year: str, month: str, day: str = "") -> list[ImageBOA]:
        source_dir = self._get_source_dir(run, year)
        output_dir = self._get_output_dir(run, year, month)

        if not source_dir.exists():
            return []

        output_dir.mkdir(parents=True, exist_ok=True)

        images: list[ImageBOA] = []

        for tif_path in source_dir.glob("*.tif"):
            if not self._matches_date(tif_path.name, year, month, day):
                continue

            png_path = output_dir / f"{tif_path.stem}.png"

            if not png_path.exists():
                self._convert_tif_to_png(tif_path, png_path)

            images.append(
                ImageBOA(
                    name=tif_path.name,
                    year=year,
                    month=month,
                    png_path=str(png_path),
                )
            )

        return images

    # ==========================
    # Funções auxiliares
    # ==========================
    def _get_source_dir(self, run: str, year: str) -> Path:
        """
        data/02_boa_images/<run>/<year>
        """
        return self.source_root / run / year

    def _get_output_dir(self, run: str, year: str, month: str) -> Path:
        """
        public/images/<run>/<year>/<month>
        """
        return self.output_root / run / year / month

    def _matches_date(self, filename: str, year: str, month: str, day: str = "") -> bool:
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
