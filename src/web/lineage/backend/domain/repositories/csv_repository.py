import csv
from pathlib import Path
import logging

logger = logging.Logger(__file__)

class CsvRepository:
    def read_elevation(self, path: str) -> list[dict]:
        file_path = Path(path)

        if not file_path.exists():
            return []

        with file_path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as file:
            reader = csv.DictReader(file)

            return [
                {
                    "elevation": float(row["cota"]),
                    "area": float(row["area"]),
                    "volume": float(row["volume"]),
                }
                for row in reader
            ]

    def read_real_volumes(self, path: str) -> list[dict]:
        file_path = Path(path)

        if not file_path.exists():
            return []

        with file_path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as file:
            reader = csv.DictReader(file)
            result = []
            for row in reader:
                elevation = -1.0
                try:
                    elevation = float(row["Cota (m)"])
                except ValueError:
                    logger.warning("Elevation info is None")

                result.append(
                    {
                        "date": row["Data da Medição"],
                        "elevation": elevation,
                        "volume": float(row["Volume Útil (hm³)"]),
                        "source": row.get(
                            "source",
                            "Arquivo CSV",
                        ),
                    }
                )

            return result
