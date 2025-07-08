from abc import ABC, abstractmethod

import numpy as np


class SpectralIndexStrategy(ABC):
    """
    Abstract base class for spectral index strategies.
    Defines the interface for calculating spectral indices from bands.
    """
    @abstractmethod
    def calculate(self, bands: np.ndarray) -> np.ndarray:
        pass

class GenericSpectralIndex(SpectralIndexStrategy):
    """
    Base class for generic spectral indices.
    This class calculates a spectral index based on two band indices:
    (b1 - b2) / (b1 + b2)
    """
    def __init__(self, b1_idx: int, b2_idx: int):
        self.b1_idx = b1_idx
        self.b2_idx = b2_idx

    def calculate(self, bands):
        b1 = bands[self.b1_idx].astype(np.float32)
        b2 = bands[self.b2_idx].astype(np.float32)
        return (b1 - b2) / (b1 + b2)

class EVI(SpectralIndexStrategy):
    def __init__(self, blue_idx: int, red_idx: int, nir_idx: int):
        self.blue_idx = blue_idx
        self.red_idx = red_idx
        self.nir_idx = nir_idx

    def calculate(self, bands):
        blue = bands[self.blue_idx].astype(np.float32)
        red = bands[self.red_idx].astype(np.float32)
        nir = bands[self.nir_idx].astype(np.float32)
        return 2.5 * (nir - red) / (nir + 6 * red - 7.5 * blue + 1)

class SpectralIndexCalculator:
    """
    Context class for calculating spectral indices using a strategy."""
    def __init__(self, strategy: SpectralIndexStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: SpectralIndexStrategy):
        self._strategy = strategy

    def calculate(self, bands: np.ndarray) -> np.ndarray:
        return self._strategy.calculate(bands)
