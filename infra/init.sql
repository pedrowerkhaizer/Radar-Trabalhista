-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Fatos CAGED (particionada por ano-mês)
CREATE TABLE IF NOT EXISTS fato_caged (
  competencia        DATE          NOT NULL,   -- 2025-01-01
  cnae2             CHAR(2)       NOT NULL,
  cbo6              CHAR(6)       NOT NULL,
  cod_municipio      CHAR(7)       NOT NULL,
  uf                CHAR(2)       NOT NULL,
  porte_empresa      SMALLINT,
  admissoes         INTEGER       NOT NULL DEFAULT 0,
  desligamentos     INTEGER       NOT NULL DEFAULT 0,
  salario_medio     NUMERIC(10,2),
  PRIMARY KEY (competencia, cnae2, cbo6, cod_municipio)
);

-- Convert to hypertable for TimescaleDB optimizations
SELECT create_hypertable('fato_caged', 'competencia', if_not_exists => TRUE);

-- Indexes for dashboard queries
CREATE INDEX IF NOT EXISTS idx_fato_caged_cnae2 ON fato_caged (competencia, cnae2);
CREATE INDEX IF NOT EXISTS idx_fato_caged_uf ON fato_caged (competencia, uf);

-- Score de compliance por CNPJ
CREATE TABLE IF NOT EXISTS compliance_score (
  cnpj_basico       CHAR(8)       PRIMARY KEY,
  score             SMALLINT      NOT NULL CHECK (score BETWEEN 0 AND 100),
  nivel_risco       TEXT          NOT NULL CHECK (nivel_risco IN ('baixo', 'medio', 'alto', 'critico')),
  score_cnj         SMALLINT,
  score_mte         SMALLINT,
  score_demissoes    SMALLINT,
  score_cadastral    SMALLINT,
  score_fgts        SMALLINT,
  calculado_em      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  detalhes          JSONB
);

-- GIN index for JSONB queries
CREATE INDEX IF NOT EXISTS idx_compliance_detalhes ON compliance_score USING GIN (detalhes);
-- Partial index for high-risk alerts
CREATE INDEX IF NOT EXISTS idx_compliance_alto_risco ON compliance_score (score) WHERE score < 50;

-- Tabela de usuários
CREATE TABLE IF NOT EXISTS users (
  id                UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  email             TEXT          UNIQUE NOT NULL,
  name              TEXT,
  avatar_url        TEXT,
  plano             TEXT          NOT NULL DEFAULT 'free' CHECK (plano IN ('free', 'pro', 'business', 'admin')),
  stripe_customer_id TEXT,
  created_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- API Keys
CREATE TABLE IF NOT EXISTS api_keys (
  id                UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID          NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  key_hash          TEXT          NOT NULL UNIQUE,  -- SHA-256 hash, never plain
  name              TEXT          NOT NULL,
  last_used_at      TIMESTAMPTZ,
  revoked_at        TIMESTAMPTZ,
  created_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- Benchmarking de Turnover por Setor (PW-49 — Fase 4, pré-calculado via dbt)
CREATE TABLE IF NOT EXISTS mart_turnover_setorial (
  id              SERIAL        PRIMARY KEY,
  cnae2           CHAR(2)       NOT NULL,
  uf              CHAR(2),                   -- NULL = nacional
  porte           SMALLINT,                  -- NULL = todos os portes
  ano_base        SMALLINT      NOT NULL,    -- ano da RAIS usada como denominador
  n_empresas      INTEGER       NOT NULL,    -- base de cálculo (mínimo 30)
  turnover_p25    NUMERIC(6,2),
  turnover_p50    NUMERIC(6,2),              -- mediana
  turnover_p75    NUMERIC(6,2),
  turnover_p90    NUMERIC(6,2),
  atualizado_em   TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  UNIQUE (cnae2, uf, porte, ano_base)
);

-- Index para lookups rápidos de benchmark
CREATE INDEX IF NOT EXISTS idx_turnover_lookup ON mart_turnover_setorial (cnae2, uf, porte, ano_base);

-- Tabelas de referência (CBO, CNAE)
CREATE TABLE IF NOT EXISTS ref_cbo (
  cbo6              CHAR(6)       PRIMARY KEY,
  descricao         TEXT          NOT NULL,
  grupo             TEXT
);

CREATE TABLE IF NOT EXISTS ref_cnae (
  cnae7             CHAR(7)       PRIMARY KEY,
  cnae2             CHAR(2)       NOT NULL,
  descricao         TEXT          NOT NULL,
  secao             TEXT
);

CREATE TABLE IF NOT EXISTS ref_municipio (
  cod_municipio     CHAR(7)       PRIMARY KEY,
  nome              TEXT          NOT NULL,
  uf                CHAR(2)       NOT NULL,
  nome_uf           TEXT
);
