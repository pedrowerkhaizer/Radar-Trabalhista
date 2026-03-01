-- mart_mercado_trabalho.sql
-- Mart: agregados por setor (CNAE 2 dígitos) e UF para o dashboard
-- PW-41: dbt models mart_mercado_trabalho

{{
  config(
    materialized='table',
    schema='marts'
  )
}}

WITH base AS (
    SELECT * FROM {{ ref('stg_caged') }}
),

por_setor_uf AS (
    SELECT
        competencia,
        cnae2,
        uf,
        SUM(admissoes)     AS admissoes,
        SUM(desligamentos) AS desligamentos,
        SUM(saldo)         AS saldo,
        AVG(salario_medio) AS salario_medio_uf
    FROM base
    GROUP BY 1, 2, 3
),

por_setor_nacional AS (
    SELECT
        competencia,
        cnae2,
        'BR'               AS uf,
        SUM(admissoes)     AS admissoes,
        SUM(desligamentos) AS desligamentos,
        SUM(saldo)         AS saldo,
        AVG(salario_medio) AS salario_medio_uf
    FROM base
    GROUP BY 1, 2
)

SELECT * FROM por_setor_uf
UNION ALL
SELECT * FROM por_setor_nacional
