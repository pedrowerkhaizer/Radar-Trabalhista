"""
Task: Download do arquivo CAGED do PDET/MTE.
"""

import os
from pathlib import Path

import aiofiles
import httpx
from prefect import task, get_run_logger

PDET_BASE_URL = "https://ftp.mtps.gov.br/pdet/microdados/NOVO%20CAGED"
DOWNLOAD_DIR = Path("/tmp/radar/caged")


@task(name="download-caged", retries=3, retry_delay_seconds=60)
def download_caged(competencia: str | None = None) -> Path:
    """
    Faz download do arquivo .7z do CAGED para a competência informada.

    Args:
        competencia: Competência no formato YYYY-MM. Se None, detecta o mais recente.

    Returns:
        Path do arquivo .7z baixado.
    """
    logger = get_run_logger()
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # TODO PW-41: implementar detecção automática da competência mais recente
    # TODO PW-41: implementar download streaming com httpx
    # TODO PW-41: implementar descompressão .7z com py7zr

    logger.info(f"Download CAGED competência: {competencia}")
    raise NotImplementedError("PW-41: implementar download CAGED")
