import json
import logging
from pathlib import Path

import ee

logger = logging.getLogger(__name__)


def authenticate_earth_engine(key_path: Path) -> None:
    try:
        with open(str(key_path.resolve()), "r") as f:
            key_data = json.load(f)

        # Pegar o email da conta de serviço
        service_account = key_data["client_email"]

        # Inicializar Earth Engine com as credenciais
        credentials = ee.ServiceAccountCredentials(
            service_account, str(key_path.resolve())
        )

        ee.Initialize(credentials)
        logger.info(f"Autenticado com a conta de serviço: {service_account}")
    except Exception as e:
        raise Exception(f"Erro ao autenticar com a conta de serviço: {e}")
