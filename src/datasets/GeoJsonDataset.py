from kedro.io import AbstractDataset
import geopandas as gpd

class GeoJsonDataSet(AbstractDataset):
    def __init__(self, filepath):
        self._filepath = filepath

    def _load(self):
        return gpd.read_file(self._filepath)

    def _save(self, data):
        data.to_file(self._filepath, driver="GeoJSON")

    def _describe(self):
        return {"filepath": self._filepath}
