"""
Pipeline ETL do CAGED — Prefect Flow principal.
PW-41: Pipeline ETL CAGED: download → validação → transformação → carga
"""

import os

from prefect import flow, get_run_logger

from tasks.download import download_caged
from tasks.load import load_caged_to_postgres
from tasks.transform import transform_caged
from tasks.validate import validate_caged_schema

# Variáveis de ambiente para notificações (opcionais)
_SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
_NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL")


def _notify_success(competencia: str, stats: dict) -> None:
    """
    Envia notificação de sucesso via Slack webhook ou email, se configurado.

    Args:
        competencia: Competência processada no formato "YYYY-MM".
        stats: Resultado retornado por load_caged_to_postgres.
    """
    import logging

    logger = logging.getLogger(__name__)

    message = (
        f"[CAGED ETL] Sucesso — competencia={competencia} | "
        f"linhas={stats.get('linhas', '?'):,} | "
        f"duracao={stats.get('duracao_s', '?')}s"
    )

    if _SLACK_WEBHOOK_URL:
        try:
            import httpx

            httpx.post(
                _SLACK_WEBHOOK_URL,
                json={"text": message},
                timeout=10.0,
            )
        except Exception as exc:
            logger.warning(f"Falha ao notificar Slack: {exc}")

    if _NOTIFY_EMAIL:
        # Placeholder: integrar com SMTP ou SendGrid conforme necessidade futura
        logger.info(f"[email placeholder] Para: {_NOTIFY_EMAIL} | {message}")


def _notify_failure(competencia: str | None, error: Exception) -> None:
    """
    Envia notificação de falha via Slack webhook, se configurado.

    Args:
        competencia: Competência que falhou (pode ser None se falhou na detecção).
        error: Exceção capturada.
    """
    import logging

    logger = logging.getLogger(__name__)

    message = (
        f"[CAGED ETL] FALHA — competencia={competencia or 'desconhecida'} | "
        f"erro={type(error).__name__}: {error}"
    )

    if _SLACK_WEBHOOK_URL:
        try:
            import httpx

            httpx.post(
                _SLACK_WEBHOOK_URL,
                json={"text": f":red_circle: {message}"},
                timeout=10.0,
            )
        except Exception as exc:
            logger.warning(f"Falha ao notificar Slack sobre erro: {exc}")


@flow(
    name="caged-etl",
    description=(
        "Pipeline ETL mensal do CAGED: "
        "download PDET → validação → transformação DuckDB → carga PostgreSQL"
    ),
    retries=2,
    retry_delay_seconds=300,
)
def caged_etl_flow(competencia: str | None = None) -> dict:
    """
    Executa o pipeline completo de ingestão do CAGED.

    Args:
        competencia: Competência no formato YYYY-MM. Se None, detecta o mais recente.

    Returns:
        dict com estatísticas da carga: {"linhas": int, "competencia": str, "duracao_s": float}

    Raises:
        Exception: qualquer falha nas tasks após retries esgotados.
    """
    logger = get_run_logger()
    logger.info(f"Iniciando pipeline CAGED para competência: {competencia or 'auto-detectar'}")

    try:
        # Etapa 1: Download streaming + descompressão .7z
        csv_path = download_caged(competencia=competencia)

        # Etapa 2: Validação de schema e integridade
        validated_path = validate_caged_schema(csv_path=csv_path)

        # Etapa 3: Transformação/aggregação com DuckDB → Parquet
        parquet_path = transform_caged(csv_path=validated_path, competencia=competencia)

        # Etapa 4: Carga no PostgreSQL via COPY (idempotente)
        stats = load_caged_to_postgres(parquet_path=parquet_path, competencia=competencia)

    except Exception as exc:
        _notify_failure(competencia, exc)
        raise

    logger.info(f"Pipeline CAGED concluído: {stats}")
    _notify_success(stats.get("competencia", competencia or "?"), stats)
    return stats


# Schedule: verifica diariamente a partir do dia 20 de cada mês
# CAGED é publicado ~dia 25 do mês seguinte à competência
if __name__ == "__main__":
    caged_etl_flow.serve(
        name="caged-etl-schedule",
        cron="0 8 20-31 * *",  # 08:00 UTC, dias 20-31 de cada mês
    )
