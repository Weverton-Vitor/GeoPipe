from abc import ABC, abstractmethod

import pandas as pd
from domain.entities.artifact import Artifact


class VolumeRepository(ABC):
    @abstractmethod
    def get_volume(self, run_name, segmentation_method) -> pd.DataFrame:
        pass


class ImageRepository(ABC):
    @abstractmethod
    def get_images(self, run_name, segmentation_method) -> pd.DataFrame:
        pass

class ArtifactRepository(ABC):
    @abstractmethod
    def get_artifacts(self, run_name, segmentation_method) -> list[Artifact]:
        pass
