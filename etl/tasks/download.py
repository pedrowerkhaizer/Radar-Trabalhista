"""Task: Download streaming do CAGED do PDET/MTE."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import py7zr
from prefect import get_run_logger, task

PDET_BASE_URL = "https://ftp.mtps.gov.br/pdet/microdados/NOVO CAGED"
DOWNLOAD_DIR = Path("/tmp/radar/caged")
CHUNK_SIZE = 1_024 * 1_024  # 1MB


@task(name="download-caged", retries=3, retry_delay_seconds=60)
def download_caged(competencia: str | None = None) -> Path:
    """
    Baixa e descomprime o arquivo CAGED do PDET para uma competência.

    Args:
        competencia: Formato "YYYY-MM". Se None, detecta o mais recente disponível.

    Returns:
        Path do arquivo CSV/TXT descomprimido.

    Raises:
        httpx.HTTPError: se download falhar após retries.
        FileNotFoundError: se arquivo não encontrado no PDET ou não extraído.
    """
    logger = get_run_logger()

    if competencia is None:
        competencia = _detect_latest_competencia()

    year, month = competencia.split("-")
    year_month = f"{year}{month}"

    out_dir = DOWNLOAD_DIR / competencia
    out_dir.mkdir(parents=True, exist_ok=True)

    # Idempotência: reutilizar se já extraído
    csv_files = list(out_dir.glob("*.txt")) + list(out_dir.glob("*.csv"))
    if csv_files:
        logger.info(f"CAGED {competencia} já baixado: {csv_files[0]}")
        return csv_files[0]

    url = f"{PDET_BASE_URL}/{year}/{year_month}/CAGEDMOV{year_month}.7z"
    archive_path = out_dir / f"CAGEDMOV{year_month}.7z"

    logger.info(f"Baixando CAGED {competencia} de {url}")

    with httpx.Client(timeout=600.0, follow_redirects=True) as client:
        with client.stream("GET", url) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(archive_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=CHUNK_SIZE):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        logger.debug(
                            f"Download: {downloaded/1e6:.1f}MB / {total/1e6:.1f}MB ({pct:.1f}%)"
                        )

    logger.info(
        f"Download concluído: {archive_path} ({archive_path.stat().st_size/1e6:.1f}MB)"
    )

    logger.info(f"Descomprimindo {archive_path}...")
    try:
        with py7zr.SevenZipFile(archive_path, mode="r") as z:
            z.extractall(path=out_dir)
    finally:
        # Limpar o .7z para economizar espaço, mesmo em caso de erro parcial
        if archive_path.exists():
            archive_path.unlink()
            logger.debug(f"Arquivo .7z removido: {archive_path}")

    csv_candidates = list(out_dir.glob("*.txt")) + list(out_dir.glob("*.csv"))
    if not csv_candidates:
        raise FileNotFoundError(
            f"Nenhum CSV/TXT encontrado em {out_dir} após descompressão"
        )

    csv_path = csv_candidates[0]
    logger.info(f"CSV extraído: {csv_path} ({csv_path.stat().st_size/1e9:.2f}GB)")
    return csv_path


def _detect_latest_competencia() -> str:
    """
    Detecta a competência mais recente disponível no PDET.

    Heurística: CAGED é publicado ~dia 25 do mês seguinte, portanto
    retorna o mês anterior ao atual como candidato seguro.

    Returns:
        Competência no formato "YYYY-MM".
    """
    today = datetime.now(timezone.utc)
    candidate = today.replace(day=1) - timedelta(days=1)
    return candidate.strftime("%Y-%m")
