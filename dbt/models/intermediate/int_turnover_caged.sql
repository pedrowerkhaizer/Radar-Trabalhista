-- int_turnover_caged.sql
-- Intermediate: volume de desligamentos por CNPJ/setor/UF/porte via CAGED
-- Base para o benchmark beta (Fase 2 / PW-48) e para mart_turnover_setorial (Fase 4 / PW-49)

{{
  config(
    materialized='ephemeral'
  )
}}

SELECT
    EXTRACT(YEAR FROM competencia)::SMALLINT  AS ano,
    cnae2,
    uf,
    porte_empresa                              AS porte,
    -- Volume total de desligamentos (proxy de turnover enquanto RAIS não disponível)
    SUM(desligamentos)                         AS total_desligamentos,
    -- Breakdown por tipo (quando disponível no CAGED)
    -- Nota: CAGED agrega desligamentos, distinção por tipo requer micro-dado
    SUM(admissoes)                             AS total_admissoes,
    AVG(salario_medio)                         AS salario_medio
FROM {{ ref('stg_caged') }}
WHERE competencia IS NOT NULL
GROUP BY 1, 2, 3, 4
