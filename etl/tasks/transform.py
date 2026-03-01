"""Task: Transformação do CAGED com DuckDB."""

from pathlib import Path

import duckdb
from prefect import get_run_logger, task

CAGED_SEPARATOR = ";"

# TipoMovimentação: < 30 = admissão, >= 30 = desligamento (codificação MTE)
ADMISSAO_THRESHOLD = 30

# Compressão Parquet: zstd oferece melhor ratio que snappy para dados tabulares densos
PARQUET_COMPRESSION = "zstd"

# Tamanho máximo de linha CSV (131072 = 128KB; linhas do CAGED são < 1KB)
CSV_MAX_LINE_SIZE = 131_072


@task(name="transform-caged")
def transform_caged(csv_path: Path, competencia: str | None = None) -> Path:
    """
    Agrega o CSV bruto do CAGED por (competencia, cnae2, cbo6, municipio, uf, porte).

    A aggregação reduz ~2M linhas para ~50-200k grupos, calculando:
    - admissoes: count de TipoMovimentação < 30
    - desligamentos: count de TipoMovimentação >= 30
    - salario_medio: média de Salário > 0 (Salário=0 é tratado como NULL)

    Args:
        csv_path: Path do CSV validado.
        competencia: Formato "YYYY-MM". Se None, extrai da coluna "Competência" do CSV.

    Returns:
        Path do arquivo Parquet com dados agregados (mesmo diretório do CSV).

    Raises:
        duckdb.Error: se a aggregação DuckDB falhar.
        FileNotFoundError: se csv_path não existir.
    """
    logger = get_run_logger()
    out_path = csv_path.parent / "aggregated.parquet"

    if out_path.exists():
        logger.info(f"Parquet já existe, reutilizando: {out_path}")
        return out_path

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV não encontrado: {csv_path}")

    logger.info(f"Transformando CAGED com DuckDB: {csv_path}")

    conn = duckdb.connect()
    try:
        # DuckDB lê o CSV lazy via VIEW — não carrega tudo em memória de uma vez
        conn.execute(f"""
            CREATE VIEW caged AS
            SELECT * FROM read_csv_auto(
                '{csv_path}',
                sep='{CAGED_SEPARATOR}',
                header=true,
                encoding='latin-1',
                ignore_errors=true,
                max_line_size={CSV_MAX_LINE_SIZE}
            )
        """)

        raw_count = conn.execute("SELECT COUNT(*) FROM caged").fetchone()[0]
        logger.info(f"Linhas brutas no CSV: {raw_count:,}")

        cols = [c[0] for c in conn.execute("DESCRIBE caged").fetchall()]
        logger.debug(f"Colunas detectadas pelo DuckDB: {cols}")

        # Aggregação principal:
        # - cnae2: primeiros 2 dígitos do IBGE Subclasse (7 dígitos → divisão CNAE)
        # - cbo6: CBOOcupação2002 com zero-padding à esquerda até 6 dígitos
        # - cod_municipio: código IBGE 7 dígitos com zero-padding
        # - uf: código UF 2 dígitos com zero-padding
        # - salario_medio: excluir Salário=0 (registros sem remuneração declarada)
        conn.execute(f"""
            COPY (
                SELECT
                    DATE_TRUNC('month',
                        MAKE_DATE(
                            CAST(SUBSTR(CAST("Competência" AS VARCHAR), 1, 4) AS INTEGER),
                            CAST(SUBSTR(CAST("Competência" AS VARCHAR), 5, 2) AS INTEGER),
                            1
                        )
                    )::DATE AS competencia,
                    LPAD(SUBSTR(CAST("IBGE Subclasse" AS VARCHAR), 1, 2), 2, '0') AS cnae2,
                    LPAD(CAST("CBOOcupação2002" AS VARCHAR), 6, '0') AS cbo6,
                    LPAD(CAST("Município" AS VARCHAR), 7, '0') AS cod_municipio,
                    LPAD(CAST("UF" AS VARCHAR), 2, '0') AS uf,
                    CAST("TamEstabLix" AS SMALLINT) AS porte_empresa,
                    SUM(CASE WHEN CAST("TipoMovimentação" AS INTEGER) < {ADMISSAO_THRESHOLD}
                             THEN 1 ELSE 0 END)::INTEGER AS admissoes,
                    SUM(CASE WHEN CAST("TipoMovimentação" AS INTEGER) >= {ADMISSAO_THRESHOLD}
                             THEN 1 ELSE 0 END)::INTEGER AS desligamentos,
                    AVG(
                        CASE WHEN CAST("Salário" AS DOUBLE) > 0
                             THEN CAST("Salário" AS DOUBLE) END
                    ) AS salario_medio
                FROM caged
                WHERE "Competência" IS NOT NULL
                  AND "Município" IS NOT NULL
                GROUP BY 1, 2, 3, 4, 5, 6
            ) TO '{out_path}' (FORMAT PARQUET, COMPRESSION '{PARQUET_COMPRESSION}')
        """)

        agg_count = conn.execute(
            f"SELECT COUNT(*) FROM read_parquet('{out_path}')"
        ).fetchone()[0]
        logger.info(
            f"Aggregação concluída: {raw_count:,} → {agg_count:,} linhas "
            f"(fator {raw_count/max(agg_count,1):.0f}x) → {out_path}"
        )

    finally:
        conn.close()

    return out_path
