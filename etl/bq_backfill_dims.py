"""
Backfill das tabelas de dimensões analíticas do CAGED.

Popula:
  - fato_caged_demog   (perfil demográfico: sexo, faixa etária, escolaridade)
  - fato_caged_rotat   (rotatividade: causa desligamento, vínculo, tempo emprego)
  - fato_caged_empresa (perspectiva empresa: porte, tipo vínculo)

Uso:
    cd etl
    uv run python bq_backfill_dims.py 2024-01 2024-12
"""
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    load_dotenv(_env_file)

from google.cloud import bigquery
import psycopg

BQ_PROJECT = os.getenv("BQ_PROJECT_ID", "")

_UF_IBGE: dict[str, str] = {
    "AC": "12", "AL": "27", "AM": "13", "AP": "16", "BA": "29",
    "CE": "23", "DF": "53", "ES": "32", "GO": "52", "MA": "21",
    "MG": "31", "MS": "50", "MT": "51", "PA": "15", "PB": "25",
    "PE": "26", "PI": "22", "PR": "41", "RJ": "33", "RN": "24",
    "RO": "11", "RR": "14", "RS": "43", "SC": "42", "SE": "28",
    "SP": "35", "TO": "17",
}


def _get_db_dsn() -> str:
    host = os.getenv("POSTGRES_HOST", "localhost")
    sslmode = "require" if "supabase.co" in host else "prefer"
    return (
        f"host={host} port={os.getenv('POSTGRES_PORT', '5432')} "
        f"dbname={os.getenv('POSTGRES_DB', 'postgres')} "
        f"user={os.getenv('POSTGRES_USER', 'postgres')} "
        f"password={os.getenv('POSTGRES_PASSWORD', '')} sslmode={sslmode}"
    )


# ── BigQuery queries ──────────────────────────────────────────────────────────

DEMOG_QUERY = """
SELECT
    DATE(CAST(ano AS INT64), CAST(mes AS INT64), 1)                          AS competencia,
    LPAD(SUBSTR(CAST(cnae_2_subclasse AS STRING), 1, 2), 2, '0')             AS cnae2,
    ANY_VALUE(sigla_uf)                                                       AS sigla_uf,
    CAST(sexo AS STRING)                                                      AS sexo,
    CASE
        WHEN CAST(idade AS INT64) < 18  THEN '<18'
        WHEN CAST(idade AS INT64) < 25  THEN '18-24'
        WHEN CAST(idade AS INT64) < 35  THEN '25-34'
        WHEN CAST(idade AS INT64) < 45  THEN '35-44'
        WHEN CAST(idade AS INT64) < 55  THEN '45-54'
        ELSE '55+'
    END                                                                       AS faixa_etaria,
    SAFE_CAST(grau_instrucao AS INT64)                                        AS grau_instrucao,
    COUNTIF(saldo_movimentacao > 0)                                           AS admissoes,
    COUNTIF(saldo_movimentacao < 0)                                           AS desligamentos,
    AVG(IF(salario_mensal > 0 AND salario_mensal < 100000, salario_mensal, NULL)) AS salario_medio
FROM `basedosdados.br_me_caged.microdados_movimentacao`
WHERE ano = @ano AND mes = @mes
GROUP BY 1, 2, 4, 5, 6
"""

ROTAT_QUERY = """
SELECT
    DATE(CAST(ano AS INT64), CAST(mes AS INT64), 1)                          AS competencia,
    LPAD(SUBSTR(CAST(cnae_2_subclasse AS STRING), 1, 2), 2, '0')             AS cnae2,
    ANY_VALUE(sigla_uf)                                                       AS sigla_uf,
    CAST(motivo_desligamento AS INT64)                                        AS causa_desligamento,
    CAST(tipo_vinculo AS INT64)                                               AS tipo_vinculo,
    CASE
        WHEN CAST(tempo_emprego AS FLOAT64) < 3   THEN '0-3m'
        WHEN CAST(tempo_emprego AS FLOAT64) < 6   THEN '3-6m'
        WHEN CAST(tempo_emprego AS FLOAT64) < 12  THEN '6-12m'
        WHEN CAST(tempo_emprego AS FLOAT64) < 24  THEN '1-2a'
        WHEN CAST(tempo_emprego AS FLOAT64) < 60  THEN '2-5a'
        ELSE '5a+'
    END                                                                       AS faixa_tempo_emprego,
    COUNTIF(saldo_movimentacao < 0)                                           AS desligamentos,
    AVG(IF(salario_mensal > 0 AND salario_mensal < 100000, salario_mensal, NULL)) AS salario_medio
FROM `basedosdados.br_me_caged.microdados_movimentacao`
WHERE ano = @ano AND mes = @mes AND saldo_movimentacao < 0
GROUP BY 1, 2, 4, 5, 6
"""

EMPRESA_QUERY = """
SELECT
    DATE(CAST(ano AS INT64), CAST(mes AS INT64), 1)                          AS competencia,
    LPAD(SUBSTR(CAST(cnae_2_subclasse AS STRING), 1, 2), 2, '0')             AS cnae2,
    ANY_VALUE(sigla_uf)                                                       AS sigla_uf,
    CAST(tamanho_estabelecimento AS INT64)                                    AS porte_empresa,
    CAST(tipo_vinculo AS INT64)                                               AS tipo_vinculo,
    COUNTIF(saldo_movimentacao > 0)                                           AS admissoes,
    COUNTIF(saldo_movimentacao < 0)                                           AS desligamentos,
    AVG(IF(salario_mensal > 0 AND salario_mensal < 100000, salario_mensal, NULL)) AS salario_medio
FROM `basedosdados.br_me_caged.microdados_movimentacao`
WHERE ano = @ano AND mes = @mes
GROUP BY 1, 2, 4, 5
"""


# ── Load helpers ──────────────────────────────────────────────────────────────

def _run_bq(client: bigquery.Client, query: str, ano: int, mes: int) -> list:
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("ano", "INT64", ano),
            bigquery.ScalarQueryParameter("mes", "INT64", mes),
        ],
        use_query_cache=True,
    )
    return list(client.query(query, job_config=job_config).result())


def _load_demog(conn: psycopg.Connection, competencia_date: str, rows: list) -> int:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM fato_caged_demog WHERE competencia = %s::date", (competencia_date,))
        cols = "competencia,cnae2,uf,sexo,faixa_etaria,grau_instrucao,admissoes,desligamentos,saldo,salario_medio"
        with cur.copy(f"COPY fato_caged_demog ({cols}) FROM STDIN") as copy:
            for r in rows:
                uf = _UF_IBGE.get(str(r.sigla_uf or ""), "00")
                saldo = int(r.admissoes or 0) - int(r.desligamentos or 0)
                sal = min(float(r.salario_medio), 9999999.99) if r.salario_medio else None
                copy.write_row((
                    competencia_date,
                    str(r.cnae2 or "00")[:2],
                    uf,
                    str(r.sexo or "9")[:1],
                    str(r.faixa_etaria or "desconhecido"),
                    int(r.grau_instrucao or 0),
                    int(r.admissoes or 0),
                    int(r.desligamentos or 0),
                    saldo,
                    sal,
                ))
    return len(rows)


def _load_rotat(conn: psycopg.Connection, competencia_date: str, rows: list) -> int:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM fato_caged_rotat WHERE competencia = %s::date", (competencia_date,))
        cols = "competencia,cnae2,uf,causa_desligamento,tipo_vinculo,faixa_tempo_emprego,desligamentos,salario_medio"
        with cur.copy(f"COPY fato_caged_rotat ({cols}) FROM STDIN") as copy:
            for r in rows:
                uf = _UF_IBGE.get(str(r.sigla_uf or ""), "00")
                sal = min(float(r.salario_medio), 9999999.99) if r.salario_medio else None
                copy.write_row((
                    competencia_date,
                    str(r.cnae2 or "00")[:2],
                    uf,
                    int(r.causa_desligamento or 0),
                    int(r.tipo_vinculo or 0),
                    str(r.faixa_tempo_emprego or "desconhecido"),
                    int(r.desligamentos or 0),
                    sal,
                ))
    return len(rows)


def _load_empresa(conn: psycopg.Connection, competencia_date: str, rows: list) -> int:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM fato_caged_empresa WHERE competencia = %s::date", (competencia_date,))
        cols = "competencia,cnae2,uf,porte_empresa,tipo_vinculo,admissoes,desligamentos,saldo,salario_medio"
        with cur.copy(f"COPY fato_caged_empresa ({cols}) FROM STDIN") as copy:
            for r in rows:
                uf = _UF_IBGE.get(str(r.sigla_uf or ""), "00")
                saldo = int(r.admissoes or 0) - int(r.desligamentos or 0)
                sal = min(float(r.salario_medio), 9999999.99) if r.salario_medio else None
                copy.write_row((
                    competencia_date,
                    str(r.cnae2 or "00")[:2],
                    uf,
                    int(r.porte_empresa or 0),
                    int(r.tipo_vinculo or 0),
                    int(r.admissoes or 0),
                    int(r.desligamentos or 0),
                    saldo,
                    sal,
                ))
    return len(rows)


# ── Main ──────────────────────────────────────────────────────────────────────

def run_backfill(client: bigquery.Client, competencias: list[str]) -> None:
    dsn = _get_db_dsn()
    for comp in competencias:
        ano, mes = map(int, comp.split("-"))
        competencia_date = f"{comp}-01"
        print(f"\n[bq_backfill_dims] ▶ {comp} ...")
        t0 = time.monotonic()
        try:
            demog_rows = _run_bq(client, DEMOG_QUERY, ano, mes)
            rotat_rows = _run_bq(client, ROTAT_QUERY, ano, mes)
            empresa_rows = _run_bq(client, EMPRESA_QUERY, ano, mes)
        except Exception as exc:
            print(f"[bq_backfill_dims] ✗ {comp}: BigQuery error — {exc}")
            continue
        with psycopg.connect(dsn) as conn:
            n1 = _load_demog(conn, competencia_date, demog_rows)
            n2 = _load_rotat(conn, competencia_date, rotat_rows)
            n3 = _load_empresa(conn, competencia_date, empresa_rows)
            conn.commit()
        elapsed = time.monotonic() - t0
        print(f"[bq_backfill_dims] ✓ {comp}: demog={n1} rotat={n2} empresa={n3} ({elapsed:.1f}s)")


def main() -> None:
    if not BQ_PROJECT:
        print("Erro: BQ_PROJECT_ID não definido no .env")
        sys.exit(1)
    client = bigquery.Client(project=BQ_PROJECT)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("Uso: uv run python bq_backfill_dims.py ANO-MES [ANO-MES_FIM]")
        sys.exit(1)
    if len(args) == 1:
        competencias = [args[0]]
    else:
        sy, sm = map(int, args[0].split("-"))
        ey, em = map(int, args[1].split("-"))
        competencias: list[str] = []
        y, m = sy, sm
        while (y, m) <= (ey, em):
            competencias.append(f"{y:04d}-{m:02d}")
            m += 1
            if m > 12:
                m, y = 1, y + 1
    print(f"[bq_backfill_dims] Competências: {competencias}")
    run_backfill(client, competencias)
    print("\n[bq_backfill_dims] Concluído!")


if __name__ == "__main__":
    main()
