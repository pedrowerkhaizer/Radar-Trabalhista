"""Task: Carga do CAGED no PostgreSQL via psycopg3 COPY."""

import os
import time
from pathlib import Path

import pandas as pd
import psycopg
from prefect import get_run_logger, task

# Colunas na ordem exata da tabela fato_caged (ver infra/init.sql)
FATO_CAGED_COLUMNS = (
    "competencia",
    "cnae2",
    "cbo6",
    "cod_municipio",
    "uf",
    "porte_empresa",
    "admissoes",
    "desligamentos",
    "salario_medio",
)

# Comprimento máximo dos campos CHAR no banco (para truncagem defensiva)
MAX_CNAE2_LEN = 2
MAX_CBO6_LEN = 6
MAX_COD_MUNICIPIO_LEN = 7
MAX_UF_LEN = 2


def _get_db_dsn() -> str:
    """
    Constrói o DSN de conexão PostgreSQL a partir de variáveis de ambiente.

    Returns:
        String DSN no formato libpq aceito pelo psycopg3.
    """
    return (
        f"host={os.getenv('POSTGRES_HOST', 'localhost')} "
        f"port={os.getenv('POSTGRES_PORT', '5432')} "
        f"dbname={os.getenv('POSTGRES_DB', 'radar_trabalhista')} "
        f"user={os.getenv('POSTGRES_USER', 'postgres')} "
        f"password={os.getenv('POSTGRES_PASSWORD', '')}"
    )


@task(name="load-caged-to-postgres", retries=2, retry_delay_seconds=30)
def load_caged_to_postgres(parquet_path: Path, competencia: str | None = None) -> dict:
    """
    Carrega o Parquet do CAGED na tabela fato_caged (operação idempotente).

    A idempotência é garantida por DELETE + COPY na mesma transação:
    deleta todas as linhas da competência e reinsere, evitando duplicatas
    em caso de reexecução do flow.

    Args:
        parquet_path: Path do Parquet com dados agregados pela task transform_caged.
        competencia: "YYYY-MM". Se None, infere da primeira linha do Parquet.

    Returns:
        dict com {"linhas": int, "competencia": str, "duracao_s": float}

    Raises:
        psycopg.Error: se a operação de banco falhar após retries.
        FileNotFoundError: se parquet_path não existir.
    """
    logger = get_run_logger()
    start = time.monotonic()

    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet não encontrado: {parquet_path}")

    df = pd.read_parquet(parquet_path)
    logger.info(f"Parquet carregado: {len(df):,} linhas de {parquet_path}")

    if competencia is None:
        # Inferir do primeiro valor da coluna competencia no Parquet
        competencia = str(df["competencia"].iloc[0])[:7]  # "YYYY-MM"

    competencia_date = f"{competencia}-01"
    logger.info(f"Competência alvo: {competencia} (date={competencia_date})")

    with psycopg.connect(_get_db_dsn()) as conn:
        with conn.cursor() as cur:
            # DELETE + COPY em mesma transação garante atomicidade
            cur.execute(
                "DELETE FROM fato_caged WHERE competencia = %s::date",
                (competencia_date,),
            )
            deleted = cur.rowcount
            if deleted > 0:
                logger.info(
                    f"Deletadas {deleted:,} linhas anteriores da competência {competencia}"
                )

            # COPY via psycopg3: protocolo binário do PostgreSQL, máxima performance
            copy_sql = (
                f"COPY fato_caged ({', '.join(FATO_CAGED_COLUMNS)}) FROM STDIN"
            )
            with cur.copy(copy_sql) as copy:
                for row in df.itertuples(index=False):
                    copy.write_row((
                        competencia_date,
                        str(row.cnae2)[:MAX_CNAE2_LEN],
                        str(row.cbo6)[:MAX_CBO6_LEN],
                        str(row.cod_municipio)[:MAX_COD_MUNICIPIO_LEN],
                        str(row.uf)[:MAX_UF_LEN],
                        int(row.porte_empresa) if pd.notna(row.porte_empresa) else None,
                        int(row.admissoes),
                        int(row.desligamentos),
                        float(row.salario_medio) if pd.notna(row.salario_medio) else None,
                    ))

        conn.commit()

    duracao = round(time.monotonic() - start, 2)
    result = {
        "linhas": len(df),
        "competencia": competencia,
        "duracao_s": duracao,
    }
    logger.info(f"Carga concluída: {result}")
    return result
