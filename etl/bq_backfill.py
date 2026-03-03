"""
Backfill do CAGED via BigQuery (basedosdados.org) → Supabase.

Usa o dataset público `basedosdados.br_me_caged` no BigQuery como fonte,
evitando dependência do FTP instável do PDET/MTE.

Uso:
    cd etl
    uv sync
    gcloud auth application-default login   # uma vez só
    uv run python bq_backfill.py --discover  # mostra tabelas disponíveis + schema
    uv run python bq_backfill.py 2024-01 2024-12  # carrega jan-dez/2024

Pré-requisitos:
    - Google Cloud project com acesso ao BigQuery (billing ativo)
    - BQ_PROJECT_ID no .env (ex: project-19be53a1-24d6-4122-aa3)
    - Credenciais: gcloud auth application-default login
"""

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# Carrega .env do diretório pai
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    load_dotenv(_env_file)

from google.cloud import bigquery  # noqa: E402
import psycopg  # noqa: E402

# ──────────────────────────────────────────────
# Configuração
# ──────────────────────────────────────────────

BQ_PROJECT = os.getenv("BQ_PROJECT_ID", "")
BD_DATASET = "basedosdados.br_me_caged"

# Mapeamento sigla UF → código IBGE 2 dígitos (mesmo que o router da API)
_UF_IBGE: dict[str, str] = {
    "AC": "12", "AL": "27", "AM": "13", "AP": "16", "BA": "29",
    "CE": "23", "DF": "53", "ES": "32", "GO": "52", "MA": "21",
    "MG": "31", "MS": "50", "MT": "51", "PA": "15", "PB": "25",
    "PE": "26", "PI": "22", "PR": "41", "RJ": "33", "RN": "24",
    "RO": "11", "RR": "14", "RS": "43", "SC": "42", "SE": "28",
    "SP": "35", "TO": "17",
}


# ──────────────────────────────────────────────
# Banco de dados
# ──────────────────────────────────────────────

def _get_db_dsn() -> str:
    host = os.getenv("POSTGRES_HOST", "localhost")
    sslmode = os.getenv(
        "POSTGRES_SSLMODE",
        "require" if "supabase.co" in host else "prefer",
    )
    return (
        f"host={host} "
        f"port={os.getenv('POSTGRES_PORT', '5432')} "
        f"dbname={os.getenv('POSTGRES_DB', 'postgres')} "
        f"user={os.getenv('POSTGRES_USER', 'postgres')} "
        f"password={os.getenv('POSTGRES_PASSWORD', '')} "
        f"sslmode={sslmode}"
    )


# ──────────────────────────────────────────────
# Discovery
# ──────────────────────────────────────────────

def cmd_discover(client: bigquery.Client) -> None:
    """Lista tabelas do dataset e mostra sample de colunas."""
    print(f"\n=== Tabelas em {BD_DATASET} ===\n")
    tables = list(client.list_tables(BD_DATASET))
    if not tables:
        print("Nenhuma tabela encontrada (verifique o billing do projeto BQ_PROJECT_ID).")
        return

    for t in tables:
        tbl = client.get_table(f"{BD_DATASET}.{t.table_id}")
        print(f"  {t.table_id}")
        print(f"    Linhas: {tbl.num_rows:,} | Tamanho: {tbl.num_bytes / 1e9:.1f} GB")
        print(f"    Colunas: {[f.name for f in tbl.schema[:10]]}{'...' if len(tbl.schema) > 10 else ''}")
        print()


# ──────────────────────────────────────────────
# Query para Novo CAGED (microdados_movimentacoes)
# ──────────────────────────────────────────────

NOVO_CAGED_QUERY = """
SELECT
    DATE(CAST(ano AS INT64), CAST(mes AS INT64), 1)                         AS competencia,
    LPAD(SUBSTR(CAST(cnae_2_subclasse AS STRING), 1, 2), 2, '0')            AS cnae2,
    LPAD(CAST(cbo_2002 AS STRING), 6, '0')                                  AS cbo6,
    LPAD(CAST(id_municipio AS STRING), 7, '0')                              AS cod_municipio,
    sigla_uf,
    CAST(tamanho_estabelecimento_jan AS INT64)                               AS porte_empresa,
    COUNTIF(tipo_movimentacao = '10' OR CAST(tipo_movimentacao AS INT64) < 30) AS admissoes,
    COUNTIF(tipo_movimentacao = '20' OR CAST(tipo_movimentacao AS INT64) >= 30) AS desligamentos,
    AVG(IF(salario_mensal > 0, salario_mensal, NULL))                        AS salario_medio
FROM `basedosdados.br_me_caged.microdados_movimentacoes`
WHERE ano = @ano AND mes = @mes
  AND id_municipio IS NOT NULL
GROUP BY 1, 2, 3, 4, 5, 6
"""

# Query para CAGED Antigo (microdados_antigos) — pré-2020, estrutura diferente
ANTIGO_CAGED_QUERY = """
SELECT
    DATE(CAST(ano AS INT64), CAST(mes AS INT64), 1)                         AS competencia,
    LPAD(SUBSTR(CAST(subclasse AS STRING), 1, 2), 2, '0')                   AS cnae2,
    LPAD(CAST(cbo AS STRING), 6, '0')                                       AS cbo6,
    LPAD(CAST(municipio AS STRING), 7, '0')                                 AS cod_municipio,
    sigla_uf,
    CAST(tam_estab AS INT64)                                                 AS porte_empresa,
    COUNTIF(LOWER(tipo_mov) LIKE '%adm%' OR saldo_movimentacao > 0)          AS admissoes,
    COUNTIF(LOWER(tipo_mov) LIKE '%desl%' OR saldo_movimentacao < 0)         AS desligamentos,
    AVG(IF(salario > 0, salario, NULL))                                      AS salario_medio
FROM `basedosdados.br_me_caged.microdados_antigos`
WHERE ano = @ano AND mes = @mes
  AND municipio IS NOT NULL
GROUP BY 1, 2, 3, 4, 5, 6
"""

FATO_CAGED_COLUMNS = (
    "competencia", "cnae2", "cbo6", "cod_municipio", "uf",
    "porte_empresa", "admissoes", "desligamentos", "salario_medio",
)


def run_backfill(
    client: bigquery.Client,
    competencias: list[str],
    table: str = "microdados_movimentacoes",
) -> None:
    query_sql = NOVO_CAGED_QUERY if table == "microdados_movimentacoes" else ANTIGO_CAGED_QUERY
    dsn = _get_db_dsn()

    for comp in competencias:
        ano, mes = comp.split("-")
        print(f"\n[bq_backfill] ▶ {comp} (ano={ano}, mes={mes}, tabela={table}) ...")
        t0 = time.monotonic()

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("ano", "STRING", ano),
                bigquery.ScalarQueryParameter("mes", "STRING", mes),
            ],
            use_query_cache=True,
        )

        try:
            job = client.query(query_sql, job_config=job_config)
            rows = list(job.result())
        except Exception as exc:
            print(f"[bq_backfill] ✗ {comp}: Erro no BigQuery — {exc}")
            # Dica se a tabela não existir
            if "microdados_movimentacoes" in str(exc) and "Not found" in str(exc):
                print("  → Tabela não encontrada. Execute com --discover para ver as disponíveis.")
                print("  → Tente: uv run python bq_backfill.py --table=microdados_antigos 2024-01 2024-12")
            continue

        if not rows:
            print(f"[bq_backfill] ⚠  {comp}: Nenhuma linha retornada (dados não disponíveis para este período?).")
            continue

        print(f"[bq_backfill]    BigQuery: {len(rows):,} linhas ({time.monotonic()-t0:.1f}s)")

        # Carrega no Supabase
        competencia_date = f"{comp}-01"
        loaded = 0
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM fato_caged WHERE competencia = %s::date",
                    (competencia_date,),
                )
                deleted = cur.rowcount
                if deleted > 0:
                    print(f"[bq_backfill]    Deletadas {deleted:,} linhas anteriores.")

                copy_sql = f"COPY fato_caged ({', '.join(FATO_CAGED_COLUMNS)}) FROM STDIN"
                with cur.copy(copy_sql) as copy:
                    for row in rows:
                        uf_ibge = _UF_IBGE.get(str(row.sigla_uf or ""), "00")
                        copy.write_row((
                            competencia_date,
                            str(row.cnae2 or "00")[:2],
                            str(row.cbo6 or "000000")[:6],
                            str(row.cod_municipio or "0000000")[:7],
                            uf_ibge,
                            int(row.porte_empresa) if row.porte_empresa is not None else None,
                            int(row.admissoes or 0),
                            int(row.desligamentos or 0),
                            float(row.salario_medio) if row.salario_medio is not None else None,
                        ))
                        loaded += 1

            conn.commit()

        duracao = round(time.monotonic() - t0, 1)
        print(f"[bq_backfill] ✓ {comp}: {loaded:,} linhas carregadas em {duracao}s")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main() -> None:
    if not BQ_PROJECT:
        print("Erro: BQ_PROJECT_ID não definido no .env")
        print("Adicione: BQ_PROJECT_ID=project-19be53a1-24d6-4122-aa3")
        sys.exit(1)

    client = bigquery.Client(project=BQ_PROJECT)

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a.lstrip("-").split("=")[0]: a.split("=")[1] if "=" in a else True
             for a in sys.argv[1:] if a.startswith("--")}

    if "discover" in flags:
        cmd_discover(client)
        return

    table = flags.get("table", "microdados_movimentacoes")

    if not args:
        print("Uso: uv run python bq_backfill.py [--discover] [--table=NOME] ANO-MES [ANO-MES_FIM]")
        print("Exemplos:")
        print("  uv run python bq_backfill.py --discover")
        print("  uv run python bq_backfill.py 2024-12")
        print("  uv run python bq_backfill.py 2024-01 2024-12")
        sys.exit(1)

    if len(args) == 1:
        competencias = [args[0]]
    elif len(args) == 2:
        # Intervalo
        start_y, start_m = map(int, args[0].split("-"))
        end_y, end_m = map(int, args[1].split("-"))
        competencias = []
        y, m = start_y, start_m
        while (y, m) <= (end_y, end_m):
            competencias.append(f"{y:04d}-{m:02d}")
            m += 1
            if m > 12:
                m = 1
                y += 1
    else:
        competencias = args

    print(f"\n[bq_backfill] Projeto BQ: {BQ_PROJECT}")
    print(f"[bq_backfill] Tabela: {BD_DATASET}.{table}")
    print(f"[bq_backfill] Competências: {competencias}")
    run_backfill(client, competencias, table=table)
    print("\n[bq_backfill] Concluído!")


if __name__ == "__main__":
    main()
