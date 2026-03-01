"""
Pipeline ETL do CAGED — Prefect Flow principal.
PW-41: Pipeline ETL CAGED: download → validação → transformação → carga
"""

from prefect import flow, get_run_logger
from prefect.schedules import CronSchedule

from tasks.download import download_caged  # noqa: F401 (imported for flow reference)
from tasks.validate import validate_caged_schema
from tasks.transform import transform_caged
from tasks.load import load_caged_to_postgres


@flow(
    name="caged-etl",
    description="Pipeline ETL mensal do CAGED: download PDET → validação → transformação DuckDB → carga PostgreSQL",
    retries=2,
    retry_delay_seconds=300,
)
def caged_etl_flow(competencia: str | None = None) -> dict:
    """
    Executa o pipeline completo de ingestão do CAGED.

    Args:
        competencia: Competência no formato YYYY-MM. Se None, usa o mês atual.

    Returns:
        dict com estatísticas da carga (linhas processadas, tempo, etc.)
    """
    logger = get_run_logger()
    logger.info(f"Iniciando pipeline CAGED para competência: {competencia or 'atual'}")

    # Etapa 1-3: Download + descompressão
    csv_path = download_caged(competencia=competencia)

    # Etapa 4: Validação de schema
    validated_path = validate_caged_schema(csv_path=csv_path)

    # Etapa 5: Transformação com DuckDB
    parquet_path = transform_caged(csv_path=validated_path, competencia=competencia)

    # Etapa 6: Carga no PostgreSQL
    stats = load_caged_to_postgres(parquet_path=parquet_path, competencia=competencia)

    logger.info(f"Pipeline CAGED concluído: {stats}")
    return stats


# Schedule: verifica diariamente a partir do dia 20 de cada mês
caged_etl_flow.serve(
    name="caged-etl-schedule",
    cron="0 8 20-31 * *",  # 08:00 UTC, dias 20-31
)
