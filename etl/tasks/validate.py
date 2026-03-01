"""
Task: Validação de schema do CAGED com Pandera.
"""

from pathlib import Path
from prefect import task, get_run_logger


@task(name="validate-caged-schema")
def validate_caged_schema(csv_path: Path) -> Path:
    """
    Valida schema do CSV do CAGED: colunas, tipos, contagem vs. mês anterior.

    Args:
        csv_path: Path do CSV descomprimido.

    Returns:
        Path do CSV validado (mesmo path, só prossegue se válido).

    Raises:
        SchemaError: se o schema não bater com o esperado.
    """
    logger = get_run_logger()
    # TODO PW-41: implementar schema Pandera para o CAGED
    # Colunas esperadas: Competência, Região, UF, Município, Setor, TipoEstabelecimento,
    #                    CNAE 2.0 Subclasse, Salário, CBOOcupação, Categoria,
    #                    GrauInstrução, Idade, Raça, Sexo, TipoDeficiência, IndCentExtr,
    #                    Porte, TipoMovimentação
    logger.info(f"Validando schema: {csv_path}")
    raise NotImplementedError("PW-41: implementar validação Pandera do CAGED")
