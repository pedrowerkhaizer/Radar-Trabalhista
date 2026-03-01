-- stg_caged.sql
-- Staging: normaliza fato_caged para uso nos marts
-- PW-41: dbt models stg_caged

{{
  config(
    materialized='view',
    schema='staging'
  )
}}

SELECT
    competencia,
    cnae2,
    cbo6,
    cod_municipio,
    uf,
    porte_empresa,
    admissoes,
    desligamentos,
    (admissoes - desligamentos) AS saldo,
    salario_medio
FROM {{ source('raw', 'fato_caged') }}
WHERE competencia IS NOT NULL
