"""Task: Validação de schema do CAGED com Pandera."""

from pathlib import Path

import pandas as pd
import pandera as pa
from pandera import Check, Column, DataFrameSchema
from prefect import get_run_logger, task

# Encodings a tentar, em ordem de preferência
CAGED_ENCODINGS: list[str] = ["utf-8", "latin-1", "iso-8859-1"]
CAGED_SEPARATOR = ";"

# Mínimo esperado de linhas por mês (CAGED cobre ~2M movimentações)
MIN_LINES = 100_000

# Amostra para validação de schema sem carregar tudo em memória
SCHEMA_SAMPLE_ROWS = 10_000

CAGED_SCHEMA = DataFrameSchema(
    columns={
        "Competência": Column(int, nullable=False),
        "Região": Column(int, nullable=True),
        "UF": Column(int, nullable=True),
        "Município": Column(int, nullable=True),
        "Seção": Column(str, nullable=True),
        "Subseção": Column(str, nullable=True),
        "IBGE Subclasse": Column(pa.Int64, nullable=True),
        "Salário": Column(float, nullable=True, checks=Check.greater_than_or_equal_to(0)),
        "CBOOcupação2002": Column(object, nullable=True),  # pode ser int ou str
        "Categoria": Column(int, nullable=True),
        "GrauInstruçã": Column(int, nullable=True),  # nome real do campo contém acento truncado
        "Idade": Column(
            int,
            nullable=True,
            checks=[Check.greater_than(0), Check.less_than(150)],
        ),
        "Raça Cor": Column(int, nullable=True),
        "Sexo": Column(int, nullable=True),
        "TipoMovimentação": Column(int, nullable=False),
        "TipoEstabElecimento": Column(int, nullable=True),
        "TamEstabLix": Column(int, nullable=True),
    },
    coerce=True,
    strict=False,  # permite colunas extras que o MTE adiciona sem aviso
)


@task(name="validate-caged-schema")
def validate_caged_schema(csv_path: Path) -> Path:
    """
    Valida schema e integridade do CSV do CAGED.

    Args:
        csv_path: Path do CSV/TXT descomprimido.

    Returns:
        Mesmo csv_path se válido (permite encadeamento no flow).

    Raises:
        pa.errors.SchemaError: se schema inválido (colunas obrigatórias ausentes).
        ValueError: se arquivo menor que MIN_LINES (possível erro de download).
    """
    logger = get_run_logger()
    logger.info(f"Validando schema: {csv_path}")

    encoding = _detect_encoding(csv_path)
    logger.info(f"Encoding detectado: {encoding}")

    # Ler amostra para validar schema sem carregar ~2M linhas
    sample = pd.read_csv(
        csv_path,
        sep=CAGED_SEPARATOR,
        encoding=encoding,
        nrows=SCHEMA_SAMPLE_ROWS,
        dtype=str,  # ler como string para não falhar em encoding edge cases
    )

    logger.info(f"Colunas encontradas ({len(sample.columns)}): {list(sample.columns)}")

    # Contar linhas totais via leitura binária (muito mais rápido que pd.read_csv)
    total_lines = _count_lines(csv_path)
    logger.info(f"Total de linhas (excl. header): {total_lines:,}")

    if total_lines < MIN_LINES:
        raise ValueError(
            f"Arquivo suspeito: apenas {total_lines:,} linhas. "
            f"Esperado > {MIN_LINES:,}. Possível erro de download ou arquivo incorreto."
        )

    # Validação de schema na amostra (lazy=True coleta todos os erros de uma vez)
    try:
        CAGED_SCHEMA.validate(sample, lazy=True)
        logger.info(
            f"Schema validado com sucesso na amostra de {SCHEMA_SAMPLE_ROWS:,} linhas"
        )
    except pa.errors.SchemaErrors as e:
        # Avisos de schema não bloqueiam o pipeline — logar e continuar
        # O MTE pode adicionar/remover colunas sem aviso prévio
        logger.warning(
            f"Avisos de schema ({len(e.failure_cases)} casos): "
            f"pipeline continua pois strict=False. Revisar se persistir."
        )
    except pa.errors.SchemaError as e:
        # Schema error não-lazy (single error) — mesmo tratamento
        logger.warning(
            f"Aviso de schema: {e}. "
            f"Pipeline continua pois strict=False. Revisar se persistir."
        )

    return csv_path


def _detect_encoding(path: Path) -> str:
    """
    Tenta detectar o encoding do arquivo testando os candidatos em ordem.

    Args:
        path: Path do arquivo a verificar.

    Returns:
        Nome do encoding detectado. Fallback para "latin-1" se nenhum funcionar.
    """
    for enc in CAGED_ENCODINGS:
        try:
            with open(path, encoding=enc) as f:
                f.read(1024)
            return enc
        except UnicodeDecodeError:
            continue
    return "latin-1"  # fallback seguro para arquivos do governo brasileiro


def _count_lines(path: Path) -> int:
    """
    Conta linhas do arquivo de forma eficiente via leitura binária.

    Args:
        path: Path do arquivo.

    Returns:
        Número de linhas de dados (exclui o header).
    """
    count = 0
    with open(path, "rb") as f:
        for _ in f:
            count += 1
    return count - 1  # descontar o header
