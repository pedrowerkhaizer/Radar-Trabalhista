## Produto — Visão Geral

Plataforma de inteligência em mercado de trabalho e compliance trabalhista.
Três módulos principais:
- **Módulo 1** — Monitor de Mercado de Trabalho (CAGED/RAIS: admissões, demissões, salário por setor/UF/CBO)
- **Módulo 2** — Score de Compliance Trabalhista (0–100 por CNPJ, cruzando CNJ + MTE + CAGED + Receita + FGTS)
- **Módulo 3** — Benchmarking de Turnover Setorial (percentil de rotatividade por setor/UF/porte via CAGED+RAIS)
- **Módulo 4** — API pública freemium (Free / Pro R$290 / Business R$990)

### 5 Personas (PM gate)

| Persona | Feature principal |
|---------|------------------|
| Analista de People Analytics | Dashboard comparativo setor × empresa + Módulo Turnover |
| HRBP / Diretor de RH | Alertas mensais CAGED + índice de rotatividade |
| M&A / Due Diligence | Score compliance + histórico CNJ por CNPJ |
| Gestor de Fornecedores | Monitoramento contínuo de CNPJs + alerta de turnover atípico |
| Consultor de RH | API + relatórios PDF exportáveis |

### Fontes de dados (escopo PM gate)

CAGED (MTE/PDET), RAIS (MTE/PDET), CNPJ Receita Federal, DataJud/CNJ, Autuações MTE, CBO e CNAE (tabelas estáticas), Municípios/UF (IBGE).
Qualquer integração fora desta lista está **fora de escopo**.

---

## Stack Tecnológico

| Camada | Tech |
|--------|------|
| ETL/Orquestração | Python 3.12 + Prefect 2 |
| Transformação | Pandas + DuckDB → PostgreSQL |
| Data Warehouse | PostgreSQL 16 + TimescaleDB |
| Modelagem DW | dbt Core |
| API Backend | FastAPI (Python 3.12) + Redis (cache) |
| Frontend | Next.js 14 (App Router) + TypeScript |
| UI | shadcn/ui + Tailwind CSS |
| Gráficos | Recharts + React-Leaflet |
| PDF | WeasyPrint (server-side) |
| Auth | OAuth2 Google + JWT (httpOnly cookie) |
| Infra | Docker Compose → Railway/Render |
| CI/CD | GitHub Actions |

---

## Estrutura do Repositório

```
apps/api/                     # FastAPI backend
  routers/                    # caged.py, compliance.py, turnover.py, auth.py, reports.py
  services/                   # scoring.py, turnover_benchmark.py, cache.py, pdf.py
  models/                     # SQLAlchemy ORM models
  schemas/                    # Pydantic request/response schemas
apps/web/                     # Next.js 14 frontend
  app/                        # App Router (layouts, pages, loading)
  components/                 # KPICard, ScoreGauge, TurnoverGauge, FilterBar, ...
  hooks/                      # useCaged.ts, useCompliance.ts, useTurnover.ts
  lib/                        # api-client.ts, auth.ts, utils.ts
etl/flows/                    # caged_flow.py, rais_flow.py, cnj_flow.py, cnpj_flow.py
etl/tasks/                    # download.py, validate.py, transform.py, load.py
dbt/models/staging/           # stg_caged.sql, stg_rais.sql, stg_cnpj.sql
dbt/models/intermediate/      # int_caged_aggregated.sql, int_turnover_cnpj.sql
dbt/models/marts/             # mart_mercado_trabalho.sql, mart_compliance.sql, mart_turnover_setorial.sql
infra/                        # docker-compose.yml, Caddyfile
docs/ADRs/                    # Architecture Decision Records
docs/runbooks/                # ETL failure, DB recovery
```

### Tabelas principais do DW

- `fato_caged` — particionada por ano-mês; grain: (competencia, cnae2, cbo6, municipio)
- `compliance_score` — score 0–100 por CNPJ com breakdown por componente (JSONB)
- `mart_turnover_setorial` — percentis p25/p50/p75/p90 por (cnae2, uf, porte, ano_base)

---

## Comandos de Desenvolvimento

```bash
# Subir todos os serviços
docker-compose up

# ETL pipeline (Prefect)
cd etl && prefect deployment run caged-flow/local

# dbt
cd dbt && dbt run && dbt test

# API local
cd apps/api && uvicorn main:app --reload

# Frontend
cd apps/web && npm run dev
```

---

## Rotas Frontend (Next.js)

| Rota | Render | Auth |
|------|--------|------|
| `/` | SSG | Não |
| `/dashboard` | CSR | Sim |
| `/setores/[slug]` | SSR | Não (SEO) |
| `/compliance` | CSR | Sim |
| `/compliance/[cnpj]` | SSR+CSR | Sim |
| `/turnover` | CSR | Sim |
| `/relatorios` | CSR | Pro |
| `/api-docs` | SSG | Não |

---

## Endpoints API principais

```
GET  /v1/caged/summary          — resumo CAGED por filtros (Free)
GET  /v1/caged/series           — série histórica mensal (Free)
GET  /v1/turnover/benchmark     — percentis de turnover por setor/UF/porte (Free)
GET  /v1/turnover/{cnpj}        — posição percentil do CNPJ (Pro)
GET  /v1/compliance/{cnpj}      — score completo (Pro)
POST /v1/compliance/batch       — score em lote até 100 CNPJs (Business)
GET  /v1/reports/{setor}/pdf    — relatório PDF de setor (Pro)
```

---

## Requisitos Não-Funcionais (metas)

- Dashboard: P95 < 2s | API simples: P95 < 500ms | Score CNPJ: < 5s | Turnover benchmark: P95 < 300ms
- Uptime: >= 99.5% | Usuários simultâneos fase inicial: 200
- LGPD: apenas dados públicos; nenhum dado de PF armazenado ou exibido

---

## Papel do Claude neste projeto

Claude atua como **Tech Lead + Product Manager** deste projeto, coordenando agentes de IA desenvolvedores via Linear MCP.

---

## Linear MCP — Coordenação de Projeto

### Regras de uso do Linear

- **Toda feature começa como issue no Linear** antes de qualquer linha de código
- **Avaliação de PM**: antes de criar uma issue, avaliar se a feature está no escopo do doc técnico (`radar_trabalhista_doc_tecnico.md`)
- **Issues fora de escopo** devem ser documentadas com label `out-of-scope` e justificativa de recusa
- **Progresso sempre atualizado**: ao iniciar uma issue → mudar para `In Progress`; ao concluir → `Done`
- **Commits linkados**: mensagens de commit devem referenciar o ID da issue Linear (ex: `PW-42: ...`)
- **Projeto Linear**: `Radar Trabalhista` (workspace `werkhz`)
- **Time**: `@verkaizer` (key: PW)

### Fluxo de trabalho padrão

```
1. Receber solicitação de feature/bug
2. Avaliar escopo vs doc técnico (PM gate)
3. Criar/atualizar issue no Linear com descrição detalhada
4. Criar branch feature/PW-{id}-{slug}
5. Implementar (agente dev)
6. Verificar critérios de aceite
7. Commit com referência ao Linear ID
8. Marcar issue como Done no Linear
```

### Milestones do projeto

| Milestone | Semanas | Target Date |
|-----------|---------|-------------|
| Fase 1 — Fundação | 1–6 | 2026-04-12 |
| Fase 2 — Compliance + Monetização | 7–14 | 2026-06-07 |
| Fase 3 — Relatórios + Alertas | 15–20 | 2026-07-19 |
| Fase 4 — Crescimento | 20+ | 2026-10-01 |

### Critério de PM gate (avaliar antes de criar issue)

Feature está no escopo se:
- Está descrita nos módulos 1, 2 ou 3 do doc técnico
- Faz parte das fases 1–4 do plano de implementação
- Serve uma das 5 personas definidas no doc

Feature está FORA do escopo se:
- Adiciona integrações não listadas nas fontes de dados (seção 4)
- Cria funcionalidades além do MVP definido por fase
- Compromete a arquitetura simples definida (seção 5)

---

## Workflow Orchestration

### 1. Plan Node Default
	•	Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
	•	If someth   ing goes sideways, STOP and re-plan immediately — don’t keep pushing
	•	Use plan mode for verification steps, not just building
	•	Write detailed specs upfront to reduce ambiguity

⸻

### 2. Subagent Strategy
	•	Use subagents liberally to keep main context window clean
	•	Offload research, exploration, and parallel analysis to subagents
	•	For complex problems, throw more compute at it via subagents
	•	One task per subagent for focused execution

⸻

### 3. Self-Improvement Loop
	•	After ANY correction from the user: update tasks/lessons.md with the pattern
	•	Write rules for yourself that prevent the same mistake
	•	Ruthlessly iterate on these lessons until mistake rate drops
	•	Review lessons at session start for relevant project

⸻

### 4. Verification Before Done
	•	Never mark a task complete without proving it works
	•	Diff behavior between main and your changes when relevant
	•	Ask yourself: “Would a staff engineer approve this?”
	•	Run tests, check logs, demonstrate correctness

⸻

### 5. Demand Elegance (Balanced)
	•	For non-trivial changes: pause and ask “is there a more elegant way?”
	•	If a fix feels hacky: “Knowing everything I know now, implement the elegant solution”
	•	Skip this for simple, obvious fixes — don’t over-engineer
	•	Challenge your own work before presenting it

⸻

### 6. Autonomous Bug Fixing
	•	When given a bug report: just fix it. Don’t ask for hand-holding
	•	Point at logs, errors, failing tests — then resolve them
	•	Zero context switching required from the user
	•	Go fix failing CI tests without being told how

⸻

## Task Management
	1.	Plan First: Write plan to tasks/todo.md with checkable items
	2.	Verify Plan: Check intent before starting implementation
	3.	Track Progress: Mark items complete as you go
	4.	Explain Changes: High-level summary at each step
	5.	Document Results: Add review section to tasks/todo.md
	6.	Capture Lessons: Update tasks/lessons.md after corrections

⸻

## Test-Driven Development (TDD) — Regra obrigatória

**Todo desenvolvimento de feature segue TDD. Sem exceção.**

### Fluxo obrigatório

```
1. Escrever o teste que descreve o comportamento esperado (RED)
2. Confirmar que o teste falha (prova que o teste é válido)
3. Implementar o mínimo de código para o teste passar (GREEN)
4. Refatorar mantendo os testes passando (REFACTOR)
5. Só marcar a issue como Done quando todos os testes passarem
```

### Por camada

| Camada | Framework | O que testar |
|--------|-----------|--------------|
| API (FastAPI) | pytest + httpx (TestClient) | endpoints, schemas, regras de negócio, rate limiting |
| Serviços/Score | pytest | cálculo do score, edge cases, componentes individuais |
| ETL | pytest + fixtures de CSV | download, validação de schema, transformação, carga idempotente |
| dbt | dbt tests (`not_null`, `unique`, `accepted_values`) | qualidade dos dados nas marts |
| Frontend | Vitest + Testing Library | componentes, hooks, integração com mock de API |

### Critério de aceite para marcar Done
- Todos os testes unitários passando
- Cobertura mínima de 70% nos novos módulos
- Testes de integração do endpoint/feature passando
- `dbt test` sem erros nas marts afetadas
- Nenhum teste existente quebrado pela mudança

---

## Core Principles
	•	Simplicity First: Make every change as simple as possible. Impact minimal code.
	•	No Laziness: Find root causes. No temporary fixes. Senior developer standards.
	•	Minimal Impact: Changes should only touch what’s necessary. Avoid introducing bugs.

⸻