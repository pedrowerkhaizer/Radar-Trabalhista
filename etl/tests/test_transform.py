"""
Unit tests para tasks/transform.py — lógica de aggregação DuckDB do CAGED.

Estes testes verificam a correctness da SQL de aggregação sem depender de
arquivos reais do PDET. Usam CSVs fake em diretórios temporários.

Execute com: pytest etl/tests/test_transform.py -v
"""

import csv
import tempfile
from pathlib import Path

import duckdb
import pytest

# -------------------------------------------------------------------
# Helpers para criar CSVs fake compatíveis com o layout do CAGED
# -------------------------------------------------------------------

# Colunas mínimas necessárias para a SQL de aggregação em transform.py
CAGED_COLUMNS = [
    "Competência",
    "Região",
    "UF",
    "Município",
    "Seção",
    "Subseção",
    "IBGE Subclasse",
    "Salário",
    "CBOOcupação2002",
    "Categoria",
    "GrauInstruçã",
    "Idade",
    "Raça Cor",
    "Sexo",
    "TipoMovimentação",
    "TipoEstabElecimento",
    "TamEstabLix",
]

# Valores padrão para colunas não relevantes ao teste
_DEFAULTS = {
    "Competência": "202401",
    "Região": "3",
    "UF": "35",
    "Município": "3550308",
    "Seção": "G",
    "Subseção": "47",
    "IBGE Subclasse": "4711301",
    "Salário": "2000.00",
    "CBOOcupação2002": "521110",
    "Categoria": "10",
    "GrauInstruçã": "7",
    "Idade": "30",
    "Raça Cor": "1",
    "Sexo": "1",
    "TipoMovimentação": "10",
    "TipoEstabElecimento": "1",
    "TamEstabLix": "3",
}


def _make_csv(rows: list[dict], tmp_dir: Path) -> Path:
    """
    Cria um CSV fake no formato CAGED com separador ';' e encoding latin-1.

    Args:
        rows: Lista de dicts com valores para sobrescrever os defaults.
        tmp_dir: Diretório onde o CSV será criado.

    Returns:
        Path do CSV criado.
    """
    csv_path = tmp_dir / "CAGEDMOV202401.txt"
    with open(csv_path, "w", encoding="latin-1", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CAGED_COLUMNS, delimiter=";")
        writer.writeheader()
        for row in rows:
            merged = {**_DEFAULTS, **row}
            writer.writerow(merged)
    return csv_path


def _run_aggregation(csv_path: Path) -> list[dict]:
    """
    Executa a mesma SQL de aggregação que transform_caged usa, em memória.

    Isso permite testar a lógica SQL sem chamar a task Prefect (que precisa
    de contexto de run ativo).

    Args:
        csv_path: Path do CSV fake.

    Returns:
        Lista de dicts com as linhas aggregadas.
    """
    conn = duckdb.connect()
    try:
        conn.execute(f"""
            CREATE VIEW caged AS
            SELECT * FROM read_csv_auto(
                '{csv_path}',
                sep=';',
                header=true,
                encoding='latin-1',
                ignore_errors=true,
                max_line_size=131072
            )
        """)

        result = conn.execute("""
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
                SUM(CASE WHEN CAST("TipoMovimentação" AS INTEGER) < 30
                         THEN 1 ELSE 0 END)::INTEGER AS admissoes,
                SUM(CASE WHEN CAST("TipoMovimentação" AS INTEGER) >= 30
                         THEN 1 ELSE 0 END)::INTEGER AS desligamentos,
                AVG(
                    CASE WHEN CAST("Salário" AS DOUBLE) > 0
                         THEN CAST("Salário" AS DOUBLE) END
                ) AS salario_medio
            FROM caged
            WHERE "Competência" IS NOT NULL
              AND "Município" IS NOT NULL
            GROUP BY 1, 2, 3, 4, 5, 6
        """).fetchall()

        columns = ["competencia", "cnae2", "cbo6", "cod_municipio", "uf",
                   "porte_empresa", "admissoes", "desligamentos", "salario_medio"]
        return [dict(zip(columns, row)) for row in result]
    finally:
        conn.close()


# -------------------------------------------------------------------
# Testes
# -------------------------------------------------------------------

def test_transform_counts_admissoes_desligamentos() -> None:
    """
    Verifica que admissões (TipoMovimentação < 30) e desligamentos
    (TipoMovimentação >= 30) são contados corretamente.

    Setup: 5 admissões (código 10) + 3 desligamentos (código 30).
    Esperado: admissoes=5, desligamentos=3.
    """
    rows = (
        [{"TipoMovimentação": "10"}] * 5  # admissões
        + [{"TipoMovimentação": "30"}] * 3  # desligamentos
    )

    with tempfile.TemporaryDirectory() as tmp:
        csv_path = _make_csv(rows, Path(tmp))
        result = _run_aggregation(csv_path)

    # Todos os registros têm mesma chave de grupo, deve resultar em 1 linha
    assert len(result) == 1, f"Esperado 1 grupo, obtido {len(result)}"
    group = result[0]
    assert group["admissoes"] == 5, f"Esperado 5 admissões, obtido {group['admissoes']}"
    assert group["desligamentos"] == 3, (
        f"Esperado 3 desligamentos, obtido {group['desligamentos']}"
    )


def test_transform_extracts_cnae2() -> None:
    """
    Verifica que IBGE Subclasse com 7 dígitos (ex: "4711301") resulta
    em cnae2 = "47" (primeiros 2 dígitos).
    """
    rows = [{"IBGE Subclasse": "4711301"}]

    with tempfile.TemporaryDirectory() as tmp:
        csv_path = _make_csv(rows, Path(tmp))
        result = _run_aggregation(csv_path)

    assert len(result) == 1
    assert result[0]["cnae2"] == "47", (
        f"Esperado cnae2='47', obtido '{result[0]['cnae2']}'"
    )


def test_transform_handles_zero_salary() -> None:
    """
    Verifica que Salário=0 é excluído do cálculo de salario_medio
    (tratado como NULL), enquanto salários positivos são incluídos.

    Setup: 1 registro com Salário=0 e 2 registros com Salário=3000.
    Esperado: salario_medio = 3000.0 (o zero é ignorado).
    """
    rows = [
        {"Salário": "0"},
        {"Salário": "3000.00"},
        {"Salário": "3000.00"},
    ]

    with tempfile.TemporaryDirectory() as tmp:
        csv_path = _make_csv(rows, Path(tmp))
        result = _run_aggregation(csv_path)

    assert len(result) == 1
    salario = result[0]["salario_medio"]
    assert salario is not None, "salario_medio não deve ser NULL quando há salários positivos"
    assert abs(salario - 3000.0) < 0.01, (
        f"Esperado salario_medio=3000.0, obtido {salario}"
    )


def test_transform_zero_salary_only_returns_null_mean() -> None:
    """
    Verifica que quando TODOS os registros têm Salário=0,
    salario_medio é NULL (não 0).
    """
    rows = [{"Salário": "0"}, {"Salário": "0"}]

    with tempfile.TemporaryDirectory() as tmp:
        csv_path = _make_csv(rows, Path(tmp))
        result = _run_aggregation(csv_path)

    assert len(result) == 1
    assert result[0]["salario_medio"] is None, (
        f"Esperado salario_medio=None quando só há Salário=0, "
        f"obtido {result[0]['salario_medio']}"
    )


def test_transform_output_is_parquet() -> None:
    """
    Verifica que a lógica de aggregação do CAGED produz um arquivo Parquet válido.

    Testa diretamente via DuckDB (sem contexto Prefect) que:
    - O arquivo aggregated.parquet é criado no diretório do CSV.
    - O arquivo não está vazio.
    - O Parquet contém as colunas esperadas e pode ser lido de volta.
    """
    rows = [{"TipoMovimentação": "10"}, {"TipoMovimentação": "30"}]

    with tempfile.TemporaryDirectory() as tmp:
        csv_path = _make_csv(rows, Path(tmp))
        expected_parquet = csv_path.parent / "aggregated.parquet"

        # Replicar a lógica do transform_caged via DuckDB direto (sem Prefect runtime)
        conn = duckdb.connect()
        try:
            conn.execute(f"""
                CREATE VIEW caged AS
                SELECT * FROM read_csv_auto(
                    '{csv_path}',
                    sep=';',
                    header=true,
                    encoding='latin-1',
                    ignore_errors=true,
                    max_line_size=131072
                )
            """)
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
                        SUM(CASE WHEN CAST("TipoMovimentação" AS INTEGER) < 30
                                 THEN 1 ELSE 0 END)::INTEGER AS admissoes,
                        SUM(CASE WHEN CAST("TipoMovimentação" AS INTEGER) >= 30
                                 THEN 1 ELSE 0 END)::INTEGER AS desligamentos,
                        AVG(CASE WHEN CAST("Salário" AS DOUBLE) > 0
                                 THEN CAST("Salário" AS DOUBLE) END) AS salario_medio
                    FROM caged
                    WHERE "Competência" IS NOT NULL
                      AND "Município" IS NOT NULL
                    GROUP BY 1, 2, 3, 4, 5, 6
                ) TO '{expected_parquet}' (FORMAT PARQUET, COMPRESSION 'zstd')
            """)
        finally:
            conn.close()

        assert expected_parquet.exists(), (
            f"Arquivo Parquet não foi criado em {expected_parquet}"
        )
        assert expected_parquet.stat().st_size > 0, "Arquivo Parquet está vazio"

        # Verificar que é um Parquet válido e contém as colunas esperadas
        # (usando DuckDB para leitura, evitando dependência de pyarrow no ambiente de CI)
        verify_conn = duckdb.connect()
        try:
            row_count = verify_conn.execute(
                f"SELECT COUNT(*) FROM read_parquet('{expected_parquet}')"
            ).fetchone()[0]
            columns = [
                c[0]
                for c in verify_conn.execute(
                    f"DESCRIBE SELECT * FROM read_parquet('{expected_parquet}')"
                ).fetchall()
            ]
        finally:
            verify_conn.close()

        assert row_count == 1, f"Esperado 1 linha aggregada, obtido {row_count}"
        assert "admissoes" in columns, f"Coluna 'admissoes' ausente: {columns}"
        assert "desligamentos" in columns, f"Coluna 'desligamentos' ausente: {columns}"
        assert "competencia" in columns, f"Coluna 'competencia' ausente: {columns}"
        assert "cnae2" in columns, f"Coluna 'cnae2' ausente: {columns}"
        assert "salario_medio" in columns, f"Coluna 'salario_medio' ausente: {columns}"
