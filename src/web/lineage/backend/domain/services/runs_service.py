from domain.repositories.run_repository import RunRepository


class RunService:
    """
    Serviço de domínio responsável por regras relacionadas às runs.
    """

    def __init__(self, run_repository: RunRepository):
        self.run_repository = run_repository

    def get_runs(self) -> list[str]:
        """
        Retorna a lista de runs disponíveis para uma etapa do pipeline.
        """

        runs = self.run_repository.list_runs()

        # regra simples, mas útil
        return sorted(runs)
