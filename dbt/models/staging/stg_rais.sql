-- stg_rais.sql
-- Staging: normaliza RAIS Vínculos para uso no mart_turnover_setorial
-- PW-49 (Fase 4) — depende do pipeline rais_flow.py

{{
  config(
    materialized='view',
    schema='staging',
    tags=['fase4', 'requires_rais_pipeline']
  )
}}

-- NOTA: Esta view depende da tabela raw.fato_rais que é populada
-- pelo pipeline etl/flows/rais_flow.py (Fase 4 / PW-49).
-- Publicação anual: maio/junho. Volume: ~50M linhas/ano.

SELECT
    cnpj_basico,
    cnae2,
    uf,
    porte_empresa                              AS porte,
    EXTRACT(YEAR FROM ano_referencia)::SMALLINT AS ano_base,
    COUNT(*)                                   AS vinculos_ativos
FROM {{ source('raw', 'fato_rais') }}
WHERE vinculo_ativo = 1
  AND cnpj_basico IS NOT NULL
GROUP BY 1, 2, 3, 4, 5
