from pathlib import Path

from domain.repositories.run_repository import RunRepository


class FileSystemRunRepository(RunRepository):
    """
    Implementação do RunRepository baseada em filesystem.

    Estrutura esperada:
    base_path/
        etapa/
            run/
                ano/
                    resultados/
    """

    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path) / "data/02_boa_images"

    def list_runs(self) -> list[str]:
        runs = [p.name for p in self.base_path.iterdir() if p.is_dir()]

        return runs
