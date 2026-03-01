-- mart_turnover_setorial.sql
-- Mart: percentis de turnover por setor/UF/porte — requer RAIS como denominador
-- PW-49 (Fase 4) — depende de stg_rais (pipeline RAIS anual)

{{
  config(
    materialized='table',
    schema='marts',
    tags=['fase4', 'requires_rais']
  )
}}

-- NOTA: Este model requer stg_rais para ser executado.
-- Fase 2: usar int_turnover_caged apenas (volume absoluto)
-- Fase 4: executar este model após pipeline RAIS anual

WITH rais_estoque AS (
    SELECT
        cnpj_basico,
        cnae2,
        uf,
        porte,
        ano_base,
        SUM(vinculos_ativos) AS estoque_medio
    FROM {{ ref('stg_rais') }}
    GROUP BY 1, 2, 3, 4, 5
),

caged_deslig AS (
    SELECT
        cnae2,
        uf,
        porte,
        ano,
        SUM(total_desligamentos) AS deslig
    FROM {{ ref('int_turnover_caged') }}
    GROUP BY 1, 2, 3, 4
),

turnover_cnpj AS (
    SELECT
        r.cnpj_basico,
        r.cnae2,
        r.uf,
        r.porte,
        r.ano_base,
        ROUND(
            c.deslig::NUMERIC / NULLIF(r.estoque_medio, 0) * 100,
            2
        ) AS turnover_pct
    FROM caged_deslig c
    JOIN rais_estoque r
        ON r.cnae2 = c.cnae2
        AND r.uf = c.uf
        AND r.porte = c.porte
        AND r.ano_base = c.ano
    WHERE c.deslig > 0
      AND r.estoque_medio > 0
)

SELECT
    cnae2,
    uf,
    porte,
    ano_base,
    COUNT(*)                                                           AS n_empresas,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY turnover_pct)        AS turnover_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY turnover_pct)        AS turnover_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY turnover_pct)        AS turnover_p75,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY turnover_pct)        AS turnover_p90
FROM turnover_cnpj
GROUP BY 1, 2, 3, 4
HAVING COUNT(*) >= 30  -- mínimo estatístico declarado na metodologia
