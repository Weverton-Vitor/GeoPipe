"""
Cloud removal pipeline with concurrent processing and pluggable reconstruction strategies.

Adding a new reconstruction algorithm:
    1. Subclass ``ImageReconstructionStrategy``.
    2. Implement ``correct_image``.
    3. Register it in ``ALGORITHM_REGISTRY``.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import rasterio

# ---------------------------------------------------------------------------
# Internal imports — adjust to your project layout
# ---------------------------------------------------------------------------
from utils.image_reconstuction.bcl import BCL

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Strategy interface
# ---------------------------------------------------------------------------


@dataclass
class CorrectionContext:
    """All data needed by any reconstruction strategy for a single image."""

    image_path: str
    mask_path: str
    output_path: str
    time_series_images_path: str
    time_series_masks_path: str
    location_name: str
    date: str
    year: int
    img_dim: tuple[int, int]
    cloud_pixels: str
    color_file_path: str
    extra: dict[str, Any]  # forward-compatibility bucket for strategy-specific params


class ImageReconstructionStrategy(ABC):
    """Abstract base for every cloud-removal / image-reconstruction algorithm."""

    @abstractmethod
    def correct_image(self, ctx: CorrectionContext) -> None:
        """
        Apply the reconstruction algorithm to the image described by *ctx*.

        Raise an exception on unrecoverable failure; the caller will log and
        skip the file.
        """

    def cleanup(self) -> None:
        """Optional teardown hook called after ``correct_image`` returns."""


# ---------------------------------------------------------------------------
# Concrete strategies
# ---------------------------------------------------------------------------


class BCLStrategy(ImageReconstructionStrategy):
    """Reconstruction using the BCL (Band Combination with Labels) algorithm."""

    def correct_image(self, ctx: CorrectionContext) -> None:
        processor = BCL(
            img_dim=ctx.img_dim,
            time_series_masks_path=ctx.time_series_masks_path,
            time_series_images_path=ctx.time_series_images_path,
            year=ctx.year,
            data=ctx.date,
            intern_reservoir=ctx.location_name,
            cloud_pixels=ctx.cloud_pixels,
            use_dec_tree=False,
            color_file_path=ctx.color_file_path,
        )
        try:
            processor.singleImageCorrection(
                target_image_path=ctx.image_path,
                target_mask_path=ctx.mask_path,
                output_path=ctx.output_path,
                image_date=ctx.date,
                image_year=ctx.year,
            )
        finally:
            processor.death()


# ---------------------------------------------------------------------------
# Example of a second strategy — add your own following this template
# ---------------------------------------------------------------------------
#
# class MyNewStrategy(ImageReconstructionStrategy):
#     """Reconstruction using <your algorithm>."""
#
#     def correct_image(self, ctx: CorrectionContext) -> None:
#         # your implementation here
#         ...


# ---------------------------------------------------------------------------
# Algorithm registry  (name → strategy instance)
# ---------------------------------------------------------------------------

ALGORITHM_REGISTRY: dict[str, ImageReconstructionStrategy] = {
    "fmask": BCLStrategy(),
    "temporal_interpolation": BCLStrategy(),
    # "my_new_algo": MyNewStrategy(),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_tiff_dimensions(tif_path: str) -> tuple[int, int]:
    """Return (height, width) of the first image in *tif_path*."""
    with rasterio.open(tif_path) as src:
        return src.height, src.width


def _extract_date(filename: str) -> str:
    """Extract and normalise the acquisition date embedded in *filename*."""
    return filename.split("_")[-1].split(".")[0].replace("-", "")


def process_single_image(
    image_file_path: str,
    mask_file_path: str,
    year: int,
    time_series_images_path: str,
    time_series_masks_path: str,
    output_path_year: str,
    color_file_log: str,
    location_name: str,
    cloud_pixels: str,
    strategy: ImageReconstructionStrategy,
    extra: dict[str, Any],
) -> str:
    """
    Process one TIFF file.  Returns the filename on success.
    Raises on unrecoverable failure so the caller can log and move on.
    """
    image_file_name = image_file_path.rsplit("/", maxsplit=1)[-1]
    img_dim = _read_tiff_dimensions(image_file_path)
    date = _extract_date(image_file_name)
    
    ctx = CorrectionContext(
        image_path=image_file_path,
        mask_path=mask_file_path,
        time_series_images_path=time_series_images_path,
        time_series_masks_path=time_series_masks_path,
        output_path=output_path_year,
        location_name=location_name,
        date=date,
        year=year,
        img_dim=img_dim,
        cloud_pixels=cloud_pixels,
        color_file_path=color_file_log,
        extra=extra,
    )

    strategy.correct_image(ctx)
    return image_file_name
