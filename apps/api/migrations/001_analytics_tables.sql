-- apps/api/migrations/001_analytics_tables.sql
-- Analytics dimension tables for Demográfico, Rotatividade, Empresa modules.
-- Run via: psql $DATABASE_URL -f apps/api/migrations/001_analytics_tables.sql

-- ── Tabela demográfica ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fato_caged_demog (
    competencia      DATE         NOT NULL,
    cnae2            CHAR(2)      NOT NULL,
    uf               CHAR(2)      NOT NULL,  -- código IBGE 2 dígitos
    sexo             CHAR(1)      NOT NULL,  -- '1'=M, '3'=F, '9'=Ignorado
    faixa_etaria     VARCHAR(10)  NOT NULL,  -- '18-24','25-34','35-44','45-54','55+'
    grau_instrucao   SMALLINT     NOT NULL,  -- 1-9 (MTE codebook)
    admissoes        INTEGER      NOT NULL DEFAULT 0,
    desligamentos    INTEGER      NOT NULL DEFAULT 0,
    saldo            INTEGER      NOT NULL DEFAULT 0,
    salario_medio    NUMERIC(10,2),
    PRIMARY KEY (competencia, cnae2, uf, sexo, faixa_etaria, grau_instrucao)
);

-- ── Tabela rotatividade ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fato_caged_rotat (
    competencia          DATE         NOT NULL,
    cnae2                CHAR(2)      NOT NULL,
    uf                   CHAR(2)      NOT NULL,
    causa_desligamento   SMALLINT     NOT NULL,  -- 11=sem justa causa, 21=pedido, etc.
    tipo_vinculo         SMALLINT     NOT NULL,  -- 10=CLT, 40=Aprendiz, etc.
    faixa_tempo_emprego  VARCHAR(10)  NOT NULL,  -- '0-3m','3-6m','6-12m','1-2a','2-5a','5a+'
    desligamentos        INTEGER      NOT NULL DEFAULT 0,
    salario_medio        NUMERIC(10,2),
    PRIMARY KEY (competencia, cnae2, uf, causa_desligamento, tipo_vinculo, faixa_tempo_emprego)
);

-- ── Tabela empresa ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fato_caged_empresa (
    competencia    DATE       NOT NULL,
    cnae2          CHAR(2)    NOT NULL,
    uf             CHAR(2)    NOT NULL,
    porte_empresa  SMALLINT   NOT NULL,  -- 1=1-10, 2=11-50, 3=51-200, 4=201-500, 5=501-1000, 6=1001+
    tipo_vinculo   SMALLINT   NOT NULL,
    admissoes      INTEGER    NOT NULL DEFAULT 0,
    desligamentos  INTEGER    NOT NULL DEFAULT 0,
    saldo          INTEGER    NOT NULL DEFAULT 0,
    salario_medio  NUMERIC(10,2),
    PRIMARY KEY (competencia, cnae2, uf, porte_empresa, tipo_vinculo)
);

-- Indexes for common filter patterns
CREATE INDEX IF NOT EXISTS idx_demog_comp_uf   ON fato_caged_demog  (competencia, uf);
CREATE INDEX IF NOT EXISTS idx_demog_comp_cnae ON fato_caged_demog  (competencia, cnae2);
CREATE INDEX IF NOT EXISTS idx_rotat_comp_uf   ON fato_caged_rotat  (competencia, uf);
CREATE INDEX IF NOT EXISTS idx_rotat_comp_cnae ON fato_caged_rotat  (competencia, cnae2);
CREATE INDEX IF NOT EXISTS idx_emp_comp_uf     ON fato_caged_empresa(competencia, uf);
CREATE INDEX IF NOT EXISTS idx_emp_comp_cnae   ON fato_caged_empresa(competencia, cnae2);
