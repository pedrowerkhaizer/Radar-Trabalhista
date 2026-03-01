"""
Task: Carga do CAGED transformado no PostgreSQL.
"""

from pathlib import Path
from prefect import task, get_run_logger


@task(name="load-caged-to-postgres")
def load_caged_to_postgres(parquet_path: Path, competencia: str | None = None) -> dict:
    """
    Carrega o Parquet agregado na tabela fato_caged (COPY + upsert).

    Args:
        parquet_path: Path do Parquet com dados transformados.
        competencia: Competência no formato YYYY-MM.

    Returns:
        dict com estatísticas: {"linhas": int, "competencia": str, "duracao_s": float}
    """
    logger = get_run_logger()
    # TODO PW-41: implementar COPY para partição do mês em fato_caged
    # usar psycopg3 copy protocol para máxima performance
    logger.info(f"Carregando CAGED no PostgreSQL: {parquet_path}")
    raise NotImplementedError("PW-41: implementar carga psycopg3 COPY do CAGED")
