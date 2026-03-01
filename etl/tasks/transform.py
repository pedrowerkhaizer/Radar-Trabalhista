"""
Task: Transformação do CAGED com DuckDB.
Agrega por (competencia, cnae2, cbo6, municipio) e calcula saldo + salário médio.
"""

from pathlib import Path
from prefect import task, get_run_logger


@task(name="transform-caged")
def transform_caged(csv_path: Path, competencia: str | None = None) -> Path:
    """
    Agrega o CSV bruto do CAGED por (competencia, cnae2, cbo6, municipio).

    Args:
        csv_path: Path do CSV validado.
        competencia: Competência no formato YYYY-MM.

    Returns:
        Path do arquivo Parquet agregado.
    """
    logger = get_run_logger()
    # TODO PW-41: implementar aggregação DuckDB
    # SQL: SELECT competencia, SUBSTR(cnae,1,2) as cnae2, cbo6, cod_municipio, uf,
    #             SUM(CASE WHEN tipo='admissao' THEN 1 ELSE 0 END) as admissoes,
    #             SUM(CASE WHEN tipo='desligamento' THEN 1 ELSE 0 END) as desligamentos,
    #             AVG(salario) as salario_medio
    #      FROM caged GROUP BY 1,2,3,4,5
    logger.info(f"Transformando CAGED: {csv_path}")
    raise NotImplementedError("PW-41: implementar transformação DuckDB do CAGED")
