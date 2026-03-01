  
🔎

**RADAR TRABALHISTA**

Plataforma de Inteligência em Mercado de Trabalho e Compliance Trabalhista

| Versão 1.0 — PRD \+ Arquitetura \+ Roadmap | Data Março 2026 |
| :---: | :---: |

Autor: Pedro Werkhaizer  |  Stack: Python · PostgreSQL · React/Next.js

# **1\. Visão Geral do Produto**

## **1.1 Problema**

O Brasil possui bases de dados trabalhistas entre as mais ricas do mundo — CAGED, RAIS, eSocial, CNPJ, CNJ — mas esse tesouro permanece fragmentado, de difícil acesso e sem integração útil. O resultado é um gap crítico em dois mercados distintos:

| Mercado | Dor Atual | Oportunidade |
| ----- | ----- | ----- |
| Profissionais de RH / People Analytics | Análises de mercado dependem de relatórios mensais rasos do MTE ou de consultorias caras | Dashboard self-service com granularidade de setor, cargo, região e tempo real |
| Empresas / Due Diligence | Auditar compliance trabalhista de fornecedores ou alvos de aquisição é processo manual e demorado | Score automatizado de risco cruzando RAIS, CAGED, CNJ e Receita Federal |
| Consultorias de RH | Benchmarking salarial depende de pesquisas pagas e desatualizadas | Acesso programático via API para enriquecer seus próprios produtos |

## **1.2 Solução**

O Radar Trabalhista é uma plataforma web que integra e processa bases de dados públicas trabalhistas do governo federal para entregar:

* Monitor de Mercado de Trabalho: movimentação de admissões, demissões, saldo e evolução salarial por setor (CNAE), ocupação (CBO), UF e município, com atualização mensal automática via pipeline CAGED/RAIS.

* Score de Compliance Trabalhista: índice de risco para CNPJs calculado a partir de ações trabalhistas no CNJ, autuações do MTE, histórico de demissões atípicas e inconsistências cadastrais.

* API pública com plano freemium para integração com sistemas de terceiros.

* Web app interativo com filtros, séries históricas, exportação e drill-down até nível de empresa.

## **1.3 Proposta de Valor por Público**

| Persona | Job to Be Done | Feature Principal |
| ----- | ----- | ----- |
| Analista de People Analytics | Benchmarking de turnover e salário vs. mercado | Dashboard comparativo setor × empresa × região |
| HRBP / Diretor de RH | Monitorar saúde do mercado para decisões de headcount | Alertas mensais por setor com variação CAGED |
| M\&A / Due Diligence | Avaliar risco trabalhista de empresa-alvo antes da compra | Score de compliance \+ histórico CNJ por CNPJ |
| Gestor de Fornecedores | Garantir que fornecedores têm compliance trabalhista | Monitoramento contínuo de CNPJs com alerta de mudança de score |
| Consultor de RH | Embasar recomendações com dados de mercado | API \+ relatórios exportáveis (PDF/Excel) |

# **2\. Requisitos Funcionais**

## **2.1 Módulo 1 — Monitor de Mercado de Trabalho**

### **2.1.1 Dashboard Principal**

* Filtros combinados: setor (CNAE 2 dígitos), ocupação (CBO), UF/Município, período (mês/ano), porte de empresa.

* KPIs principais: saldo líquido de empregos, total de admissões, total de demissões, salário mediano de admissão.

* Evolução temporal: gráfico de linha com série histórica configurável (3, 12, 24, 60 meses).

* Mapa de calor geográfico: saldo por UF e município com legenda de intensidade.

* Ranking de setores: tabela com top 10 setores em saldo, crescimento % e salário mediano.

* Comparador: selecionar até 3 setores/regiões para análise paralela.

### **2.1.2 Drill-down de Ocupações (CBO)**

* Tabela de ocupações dentro de um setor filtrado com: CBO, nome, admissões, demissões, saldo, salário mediano.

* Visualização de pirâmide etária de admitidos por ocupação.

* Escolaridade: distribuição de admissões por nível de instrução.

### **2.1.3 Alertas e Relatórios**

* Relatório mensal automático: após publicação do CAGED, sistema gera resumo executivo por setor selecionado (PDF e email).

* Exportação: qualquer tabela/gráfico exportável em CSV, Excel e PNG.

* Relatório completo de setor (PDF): 3–5 páginas com análise gerada automaticamente incluindo variação histórica, top municípios e principais ocupações.

## **2.2 Módulo 2 — Score de Compliance Trabalhista**

### **2.2.1 Busca por CNPJ**

* Input de CNPJ → retorna ficha completa com: razão social, porte, CNAE principal, UF, situação cadastral na Receita Federal.

* Score de Compliance (0–100) calculado em tempo real a partir das fontes abaixo.

* Histórico de variação do score nos últimos 12 meses.

### **2.2.2 Componentes do Score**

| Componente | Fonte | Peso | Descrição |
| ----- | ----- | ----- | ----- |
| Ações Trabalhistas | CNJ (DataJud) | 30% | Número de processos ativos/encerrados, valor em disputa, natureza das ações |
| Autuações MTE | Portal da Transparência / MTE | 25% | Infrações registradas no histórico de fiscalizações do Ministério do Trabalho |
| Demissões Atípicas | CAGED \+ RAIS cruzado | 20% | Picos de demissão sem justa causa acima de 2 desvios padrão do setor |
| Saúde Cadastral | Receita Federal (CNPJ) | 15% | Regularidade fiscal, tempo de atividade, situação cadastral |
| Regularidade FGTS | CEF (dados públicos) | 10% | CND-FGTS e histórico de débitos abertos |

### **2.2.3 Output do Score**

* Badge de risco: Baixo (verde, 75–100), Médio (amarelo, 50–74), Alto (laranja, 25–49), Crítico (vermelho, 0–24).

* Breakdown detalhado: pontuação e justificativa por componente.

* Linha do tempo: eventos relevantes que impactaram o score (ação aberta, autuação, demissão em massa).

* Empresas relacionadas: outros CNPJs do mesmo grupo econômico com seus respectivos scores.

* Exportação em PDF: relatório de due diligence formatado pronto para apresentação.

## **2.3 Módulo 3 — API Pública**

### **2.3.1 Endpoints Principais**

| Método | Endpoint | Descrição | Plano |
| ----- | ----- | ----- | ----- |
| GET | /v1/caged/summary | Resumo CAGED por filtros (setor, UF, período) | Free |
| GET | /v1/caged/series | Série histórica mensal com parâmetros | Free |
| GET | /v1/cbo/occupations | Lista de CBO com dados agregados por setor | Free |
| GET | /v1/compliance/{cnpj} | Score completo de compliance por CNPJ | Pro |
| GET | /v1/compliance/{cnpj}/history | Histórico de score e eventos | Pro |
| POST | /v1/compliance/batch | Score em lote para lista de CNPJs (max 100\) | Business |
| GET | /v1/reports/{setor}/pdf | Relatório PDF de setor gerado dinamicamente | Pro |
| GET | /v1/alerts/subscribe | Webhook para alertas de mudança de score | Business |

### **2.3.2 Autenticação e Rate Limits**

| Plano | Custo | Req/min | CNPJ/mês | API Score | Relatório PDF |
| ----- | ----- | ----- | ----- | ----- | ----- |
| Free | R$ 0 | 30 | — | Não | Não |
| Pro | R$ 290/mês | 120 | 500 | Sim | Sim |
| Business | R$ 990/mês | 600 | Ilimitado | Sim | Sim \+ Webhook |

# **3\. Requisitos Não-Funcionais**

| Categoria | Requisito | Meta |
| ----- | ----- | ----- |
| Performance | Tempo de resposta de consultas no dashboard | \< 2 segundos (P95) |
| Performance | Tempo de resposta da API (endpoint simples) | \< 500ms (P95) |
| Performance | Score de compliance por CNPJ (cálculo em tempo real) | \< 5 segundos |
| Disponibilidade | Uptime da plataforma web | ≥ 99.5% |
| Escalabilidade | Suporte a usuários simultâneos (fase inicial) | 200 usuários |
| Escalabilidade | Volume de dados CAGED (registros mensais) | \~2 milhões de linhas/mês |
| Segurança | Autenticação de usuários | JWT \+ OAuth2 (Google/LinkedIn) |
| Segurança | Dados de API keys | Hash bcrypt, nunca em logs |
| Segurança | LGPD | Apenas dados públicos; nenhum dado pessoal de PF armazenado |
| Observabilidade | Logging estruturado | JSON com tracing distribuído (request\_id) |
| Observabilidade | Monitoramento de pipeline ETL | Alertas por email/Slack em falha |
| SEO / Público | Páginas de setor (ex: /setores/construcao-civil) | Server-side rendered (Next.js SSR) |

# **4\. Fontes de Dados**

## **4.1 Bases Primárias (Ingestão Automática)**

| Base | Órgão | Formato | Frequência | Volume estimado |
| ----- | ----- | ----- | ----- | ----- |
| CAGED (Novo) | MTE / PDET | CSV compactado (.7z) | Mensal (\~25 do mês) | \~2M linhas/mês |
| RAIS Vínculos | MTE / PDET | CSV compactado (.7z) | Anual (mai/jun) | \~50M linhas/ano |
| CNPJ Receita Federal | Receita Federal | CSV particionado | Mensal (1ª semana) | \~60M registros |
| DataJud (CNJ) | CNJ | API REST \+ JSON | Diário (delta) | \~120M processos total |
| Autuações MTE | Portal da Transparência | CSV / API | Mensal | \~500k registros |
| CBO (tabela) | MTE | XLSX estático | Eventual (rare) | \~2.500 ocupações |
| CNAE (tabela) | IBGE | XLSX estático | Eventual | \~1.300 classes |
| Municípios / UF | IBGE | API REST | Eventual | 5.570 municípios |

## **4.2 Considerações Legais e de LGPD**

| Conformidade com LGPD O Radar Trabalhista opera exclusivamente com dados abertos publicados pelo Poder Público com base no art. 7º, § 3º e art. 23 da LGPD. Nenhum dado de pessoa física identificável (CPF, nome, endereço) é armazenado ou exibido. Dados são agregados ou referentes a pessoas jurídicas. CNPJs são dados públicos por natureza (art. 4º da Lei 13.709/2018). O sistema não realiza perfilamento individual de trabalhadores. |
| :---- |

## **4.3 Estratégia de Atualização**

* CAGED: cron job mensal acionado automaticamente após publicação no site do PDET. Fallback: verificação diária a partir do dia 20\.

* RAIS: pipeline de ingestão anual com validação de checksum. Processo mais pesado rodando em horário off-peak.

* CNPJ: atualização mensal incremental (somente CNPJs já monitorados \+ novos no período).

* DataJud: chamadas incrementais via API do CNJ com cursor de data de atualização.

* Tabelas estáticas (CBO, CNAE): versionadas no repositório, atualizadas sob demanda.

# **5\. Arquitetura Técnica**

## **5.1 Visão Geral da Arquitetura**

| Princípio de Design Arquitetura orientada a dados com separação clara entre camadas de ingestão (ETL), armazenamento analítico, API de serviço e frontend. Favorece simplicidade e baixo custo operacional para estágio inicial, com caminho de crescimento horizontal bem definido. |
| :---- |

Fluxo de dados macroscópico:

**Fontes Públicas  →  ETL (Python)  →  Data Warehouse (PostgreSQL)  →  API (FastAPI)  →  Web App (Next.js)**

## **5.2 Stack Tecnológico Completo**

| Camada | Tecnologia | Justificativa |
| ----- | ----- | ----- |
| Ingestão / ETL | Python 3.12 \+ Prefect 2 | Orquestração de pipelines com retry, logging e agendamento. Familiaridade prévia com Python. |
| Extração / HTTP | httpx \+ aiofiles | Requisições assíncronas para APIs e download de arquivos grandes com stream. |
| Transformação | Pandas \+ DuckDB | Pandas para transformações; DuckDB para queries analíticas em arquivos CSV/Parquet antes de carregar no Postgres. |
| Data Warehouse | PostgreSQL 16 \+ TimescaleDB | TimescaleDB adiciona compressão e funções de séries temporais nativas ao Postgres. Familiar via stack atual. |
| Modelagem de DW | dbt Core | Versionamento de transformações SQL, testes automáticos de qualidade e lineage de dados. |
| API Backend | Python 3.12 \+ FastAPI | Alta performance async, tipagem com Pydantic, OpenAPI gerado automaticamente. |
| Cache de API | Redis 7 | Cache de queries frequentes (ex: CAGED nacional do mês corrente) com TTL configurável. |
| Autenticação | FastAPI \+ OAuth2 (Google) \+ JWT | Login social para fricção mínima. JWT com refresh token armazenado em httpOnly cookie. |
| Frontend | Next.js 14 (App Router) | SSR para páginas de setor (SEO), RSC para performance, TypeScript. |
| Componentes UI | shadcn/ui \+ Tailwind CSS | Componentes acessíveis e customizáveis. Sem dependência de biblioteca de design pesada. |
| Gráficos | Recharts \+ React-Leaflet | Recharts para séries temporais/barras. Leaflet para mapa coroplético de UFs. |
| Tabelas | TanStack Table v8 | Paginação, ordenação e filtros server-side para tabelas grandes. |
| Geração de PDF | WeasyPrint (Python) | Geração de relatórios PDF via HTML/CSS no servidor. Simples e sem dependência de browser headless. |
| Infraestrutura | Docker \+ Docker Compose | Ambiente de desenvolvimento reproduzível. Deploy via Railway ou Render (fase inicial). |
| Monitoramento | Sentry \+ Prometheus \+ Grafana | Sentry para erros; Prometheus \+ Grafana para métricas de pipeline e API. |
| CI/CD | GitHub Actions | Pipeline de testes, linting e deploy automatizado. |

## **5.3 Modelagem do Data Warehouse (PostgreSQL)**

### **Esquema de tabelas principais**

\-- Fatos CAGED (particionada por ano-mês)  
CREATE TABLE fato\_caged (  
  competencia        DATE          NOT NULL,   \-- 2025-01-01  
  cnae2             CHAR(2)       NOT NULL,  
  cbo6              CHAR(6)       NOT NULL,  
  cod\_municipio      CHAR(7)       NOT NULL,  
  uf                CHAR(2)       NOT NULL,  
  porte\_empresa      SMALLINT,  
  admissoes         INTEGER       NOT NULL DEFAULT 0,  
  desligamentos     INTEGER       NOT NULL DEFAULT 0,  
  salario\_medio     NUMERIC(10,2),  
  PRIMARY KEY (competencia, cnae2, cbo6, cod\_municipio)  
) PARTITION BY RANGE (competencia);

\-- Score de compliance por CNPJ (atualizado incrementalmente)  
CREATE TABLE compliance\_score (  
  cnpj\_basico       CHAR(8)       PRIMARY KEY,  
  score             SMALLINT      NOT NULL,  \-- 0 a 100  
  nivel\_risco       TEXT          NOT NULL,  \-- baixo/medio/alto/critico  
  score\_cnj         SMALLINT,  
  score\_mte         SMALLINT,  
  score\_demissoes    SMALLINT,  
  score\_cadastral    SMALLINT,  
  score\_fgts        SMALLINT,  
  calculado\_em      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),  
  detalhes          JSONB  
);

| Estratégia de Indexação Índices compostos em (competencia, cnae2) e (competencia, uf) na fato\_caged para queries de dashboard. Índice GIN em detalhes (JSONB) no compliance\_score para busca em sub-componentes. Partial index em score \< 50 para alertas de risco. |
| :---- |

## **5.4 Pipeline ETL — Diagrama de Fluxo CAGED**

| Etapa | Processo | Tecnologia | SLA |
| ----- | ----- | ----- | ----- |
| 1\. Trigger | Cron verifica publicação no PDET (dia 20–28) | Prefect scheduled flow | Diário |
| 2\. Download | Download do arquivo .7z (\~800MB comprimido) | httpx streaming | \< 10min |
| 3\. Descompressão | Extração do CSV (\~8GB descomprimido) | Python 7z lib | \< 5min |
| 4\. Validação | Schema check: colunas, tipos, contagem de linhas vs. mês anterior | Pandera / dbt tests | \< 2min |
| 5\. Transformação | Aggregação por (competencia, cnae2, cbo6, municipio), cálculo de saldo e salário médio | DuckDB in-memory SQL | \< 8min |
| 6\. Carga | COPY para partição do mês no Postgres \+ upsert em caso de reprocessamento | psycopg3 COPY | \< 3min |
| 7\. dbt run | Atualização de marts (tabelas agregadas por UF, setor, nacional) | dbt Core | \< 5min |
| 8\. Cache bust | Invalidação de keys Redis do mês atual | Redis SCAN \+ DEL | \< 30s |
| 9\. Notificação | Email/Slack para admin \+ usuários inscritos em alertas mensais | SendGrid / Slack webhook | \< 1min |

# **6\. Arquitetura do Frontend (Next.js 14\)**

## **6.1 Estrutura de Rotas**

| Rota | Tipo de Render | Descrição |
| ----- | ----- | ----- |
| / | SSG | Landing page com valor do produto, CTA de cadastro e preview de dados públicos |
| /dashboard | CSR (auth required) | Monitor de mercado principal com todos os filtros |
| /setores/\[slug\] | SSR | Página de setor pública (ex: /setores/construcao-civil) — SEO-friendly |
| /compliance | CSR (auth required) | Busca e score de compliance por CNPJ |
| /compliance/\[cnpj\] | SSR \+ CSR hydration | Página do CNPJ com score, histórico e eventos |
| /api-docs | SSG | Documentação interativa da API (Swagger UI embutido) |
| /relatorios | CSR (pro required) | Geração e histórico de relatórios PDF |
| /configuracoes | CSR (auth required) | API keys, preferências de alerta, plano |

## **6.2 Componentes-Chave**

### **Dashboard (Monitor de Mercado)**

* FilterBar: componente de filtros persistente no topo com estado sincronizado via URL (searchParams). Permite compartilhamento de links com filtros aplicados.

* KPICard: card reutilizável com valor principal, variação percentual vs. período anterior e sparkline de 12 meses.

* CAGEDChart: gráfico de barras empilhadas (admissões / desligamentos) com linha de saldo. Recharts \+ Tailwind.

* MapaUF: mapa coroplético do Brasil com react-leaflet usando GeoJSON das UFs. Hover mostra tooltip com KPIs.

* SetorRanking: tabela TanStack com ordenação client-side, virtualização de linhas e exportação.

### **Compliance**

* CNPJSearch: input com validação de CNPJ em tempo real e debounce de 400ms antes de disparar API.

* ScoreGauge: gauge semicircular animado com gradiente verde-vermelho e label de nível de risco.

* ScoreBreakdown: accordion com pontuação por componente \+ justificativa expandível.

* TimelineEventos: linha do tempo vertical com eventos que impactaram o score (ações, autuações).

## **6.3 Gestão de Estado e Data Fetching**

* TanStack Query (React Query): fetching, cache, refetch automático e loading states para todos os dados remotos.

* Zustand: estado global leve para filtros do dashboard e preferências de UI.

* Server Actions (Next.js 14): submissão de formulários (cadastro, alertas) sem API route separada.

* Optimistic updates: ao assinar plano ou configurar alerta, UI atualiza imediatamente com rollback em caso de erro.

# **7\. Segurança e Conformidade**

| Área | Implementação |
| ----- | ----- |
| Autenticação | OAuth2 via Google (login social). JWT access token (15min) \+ refresh token (7 dias) em httpOnly cookie. Sem armazenamento de senhas. |
| Autorização | RBAC simples: roles free, pro, business, admin. Middleware Next.js verifica JWT em rotas protegidas. FastAPI dependency injection verifica plano do usuário. |
| API Keys | Geradas com secrets.token\_urlsafe(32). Armazenadas como SHA-256 hash no banco. Nunca expostas em logs. Rotação disponível no dashboard. |
| Rate Limiting | Redis sliding window por API key e por IP. Retorno 429 com header Retry-After. |
| Dados sensíveis | Nenhum dado de PF armazenado. CNPJs são públicos. Sem armazenamento de CPF, nome ou endereço de trabalhadores. |
| HTTPS | TLS 1.3 obrigatório. HSTS habilitado. Certificado Let's Encrypt via Caddy (reverse proxy). |
| SQL Injection | Exclusivamente queries parametrizadas via SQLAlchemy / psycopg3. Nenhuma string interpolada em SQL. |
| XSS / CSRF | Next.js com Content-Security-Policy. CSRF token em mutations via Server Actions. Sanitização de outputs com DOMPurify. |
| Dependências | Dependabot habilitado. pip-audit e npm audit no CI. Atualizações semanais automáticas para patches de segurança. |

# **8\. Plano de Implementação Faseado**

| Filosofia de Entrega Cada fase entrega valor independente e pode ser validada com usuários reais antes de avançar. A monetização entra na Fase 2, não na Fase 3, para testar disposição a pagar cedo. Fases são estimativas; ajuste conforme sua disponibilidade de tempo. |
| :---- |

## **Fase 1 — Fundação (Semanas 1–6)**

Objetivo: Pipeline ETL funcionando \+ dashboard básico do Monitor de Mercado ao ar (público, sem autenticação).

| Semana | Entregável | Critério de Aceite |
| ----- | ----- | ----- |
| 1–2 | Setup de infra: Postgres \+ TimescaleDB \+ Docker Compose \+ repositório GitHub com CI básico | docker-compose up sobe todos os serviços; GitHub Actions roda linting |
| 2–3 | Pipeline CAGED: download, descompressão, validação, carga na fato\_caged | Dados de 12 meses históricos carregados; dbt run sem erros; total de linhas confere com PDET |
| 3–4 | API FastAPI: endpoints /caged/summary e /caged/series com cache Redis | Swagger UI acessível; P95 \< 500ms em testes locais; cobertura de testes \> 70% |
| 4–5 | Frontend Next.js: Landing page \+ Dashboard com KPICards \+ CAGEDChart \+ filtros de setor e UF | Deploy no Railway/Render; dashboard carrega em \< 3s; filtros funcionando |
| 5–6 | MapaUF \+ SetorRanking \+ exportação CSV | Mapa renderiza corretamente; exportação CSV funciona; mobile-friendly |

## **Fase 2 — Compliance \+ Monetização (Semanas 7–14)**

Objetivo: Score de compliance ao ar \+ autenticação \+ planos pagos com Stripe. Primeiros R$ em MRR.

| Semana | Entregável | Critério de Aceite |
| ----- | ----- | ----- |
| 7–8 | Ingestão CNJ (DataJud) \+ CNPJ Receita Federal: pipelines de extração incremental | CNPJs do setor de construção civil carregados com dados CNJ vinculados |
| 8–9 | Motor de scoring: algoritmo de cálculo dos 5 componentes \+ tabela compliance\_score | Score calculado para 1.000 CNPJs; distribuição estatística esperada (maioria entre 60–80) |
| 9–10 | Frontend Compliance: CNPJSearch \+ ScoreGauge \+ ScoreBreakdown \+ TimelineEventos | Busca retorna resultado em \< 5s; layout responsivo; exportação PDF funciona |
| 10–11 | Autenticação: OAuth2 Google \+ JWT \+ rotas protegidas \+ RBAC | Login/logout funcionando; refresh automático; middleware bloqueando rotas sem auth |
| 11–12 | Stripe: planos Free/Pro/Business \+ webhook de pagamento \+ upgrade de plano | Pagamento de teste processado; plano atualizado automaticamente; recibo por email |
| 12–13 | API Keys: geração, listagem, revogação \+ rate limiting por plano | API Key gerada no dashboard; rate limit 429 retornado corretamente por plano |
| 13–14 | Pipeline MTE autuações \+ integração no score \+ ajuste de pesos | Score reflete autuações MTE; A/B test manual com 10 CNPJs conhecidos valida lógica |

## **Fase 3 — Relatórios \+ Alertas \+ Polimento (Semanas 15–20)**

Objetivo: produto completo com relatórios PDF, alertas mensais e qualidade de produção.

| Semana | Entregável | Critério de Aceite |
| ----- | ----- | ----- |
| 15–16 | Geração de relatório PDF de setor (WeasyPrint) \+ endpoint /reports/{setor}/pdf | PDF de 5 páginas gerado em \< 10s; formatação profissional; dados corretos |
| 16–17 | Sistema de alertas mensais: email após publicação CAGED \+ alerta de mudança de score de CNPJ | Email chega em \< 1h após pipeline; usuário consegue configurar CNPJs monitorados |
| 17–18 | API pública documentada (Swagger \+ README) \+ batch endpoint para CNPJs | Docs acessíveis; batch de 100 CNPJs retorna em \< 30s |
| 18–19 | Páginas de setor SSR (/setores/\[slug\]) para SEO \+ sitemap gerado automaticamente | Lighthouse SEO score \> 90; página indexada pelo Google Search Console |
| 19–20 | Observabilidade: Sentry \+ Prometheus \+ Grafana \+ runbook de incidentes | Dashboard Grafana mostrando métricas de pipeline e API; alerta de falha de ETL funcionando |

## **Fase 4 — Crescimento (Pós-semana 20\)**

* RAIS: ingestão anual e funcionalidades de vínculo empregatício histórico.

* Integração de dados de CBO com nomes em português e categorias de skill.

* API de webhook: notificação push para clientes Business quando score de CNPJ monitorado muda.

* White-label: relatórios com logo do cliente para consultorias de RH.

* Integração com LinkedIn/Gupy para enriquecer dados de vagas publicadas vs. contratações CAGED.

# **9\. Estrutura do Repositório**

**radar-trabalhista/**

├── apps/

│   ├── api/                  \# FastAPI backend

│   │   ├── routers/          \# caged.py, compliance.py, auth.py, reports.py

│   │   ├── services/         \# scoring.py, cache.py, pdf.py

│   │   ├── models/           \# SQLAlchemy ORM models

│   │   ├── schemas/          \# Pydantic request/response schemas

│   │   └── main.py

│   └── web/                  \# Next.js 14 frontend

│       ├── app/              \# App Router (layouts, pages, loading)

│       ├── components/       \# KPICard, ScoreGauge, FilterBar, ...

│       ├── lib/              \# api-client.ts, auth.ts, utils.ts

│       └── hooks/            \# useCaged.ts, useCompliance.ts

├── etl/                      \# Pipelines Prefect

│   ├── flows/                \# caged\_flow.py, cnpj\_flow.py, cnj\_flow.py

│   ├── tasks/                \# download.py, validate.py, transform.py, load.py

│   └── schedules/            \# schedule definitions

├── dbt/                      \# dbt project

│   ├── models/

│   │   ├── staging/          \# stg\_caged.sql, stg\_cnpj.sql

│   │   ├── intermediate/     \# int\_caged\_aggregated.sql

│   │   └── marts/            \# mart\_mercado\_trabalho.sql, mart\_compliance.sql

│   └── tests/                \# data quality tests

├── infra/

│   ├── docker-compose.yml    \# Postgres, Redis, API, Web, Prefect

│   └── caddy/Caddyfile       \# Reverse proxy \+ TLS

├── .github/workflows/

│   ├── ci.yml                \# lint, test, type-check

│   └── deploy.yml            \# deploy to Railway on merge to main

└── docs/

    ├── ADRs/                 \# Architecture Decision Records

    └── runbooks/             \# ETL failure, DB recovery

# **10\. Estratégia de Monetização**

## **10.1 Projeção Conservadora de MRR**

| Mês | Clientes Free | Clientes Pro (R$290) | Clientes Business (R$990) | MRR Est. |
| ----- | ----- | ----- | ----- | ----- |
| M1–M3 (Fase 2\) | 50–100 | 3–5 | 0 | R$ 870–1.450 |
| M4–M6 | 200+ | 10–15 | 1–2 | R$ 3.880–6.330 |
| M7–M12 | 500+ | 25–35 | 4–6 | R$ 11.210–15.710 |

## **10.2 Canais de Aquisição**

* SEO orgânico: páginas /setores/\[slug\] ranqueando para termos como "mercado de trabalho construção civil 2025".

* LinkedIn: posts mensais com análise do CAGED \+ visualizações atrativas. Público natural: HRBPs, People Analytics, M\&A.

* Parcerias com consultorias de RH: modelo de revenda white-label (30% de comissão sobre plano Business).

* Product Hunt: lançamento público na conclusão da Fase 1 para tração inicial e feedback.

* Comunidades: grupos de People Analytics no LinkedIn e Slack (ex: People Analytics Brasil).

## **10.3 Métricas de Sucesso (OKRs Fase 2\)**

| Métrica | Meta ao Final da Fase 2 (Semana 14\) |
| ----- | ----- |
| MRR | R$ 1.000 (ao menos 3 clientes pagantes) |
| Usuários cadastrados (free) | 100 |
| CNPJs consultados no compliance | 500 |
| Churn mensal (clientes pro) | \< 10% |
| NPS (survey in-app) | \> 30 |
| Uptime | ≥ 99.5% |

# **11\. Riscos e Mitigações**

| Risco | Probabilidade | Impacto | Mitigação |
| ----- | ----- | ----- | ----- |
| Mudança no formato de arquivo CAGED pelo PDET | Média | Alto | Validação de schema em toda ingestão (Pandera). Notificação automática ao admin em caso de falha. Monitoramento de changelog do PDET. |
| API DataJud (CNJ) instável ou com rate limit baixo | Alta | Médio | Fila de retry com backoff exponencial. Cache agressivo dos resultados. Fallback: processar CNPJs em lotes noturnos. |
| Score de compliance gera falso positivo relevante e empresa reclama | Baixa | Alto | Linguagem de "indicadores de risco" nunca "acusatória". Disclaimer claro nas páginas. Botão de "contestar dado" para envio ao admin. |
| Concorrência de players estabelecidos (Neoway, Serasa) | Média | Médio | Foco em nicho trabalhista específico e preço acessível. Diferencial em transparência de fontes e UX superior. |
| Crescimento de infraestrutura além do esperado | Baixa | Médio | TimescaleDB comprime dados históricos automaticamente. Particionamento da fato\_caged permite arquivar partições antigas. Railway escala vertical facilmente. |
| Disponibilidade de tempo do autor para manter o projeto | Média | Alto | Arquitetura simples e bem documentada. ADRs registradas. Automação máxima do pipeline ETL para reduzir manutenção manual. |

# **12\. Glossário e Referências**

## **12.1 Glossário**

| Termo | Definição |
| ----- | ----- |
| CAGED | Cadastro Geral de Empregados e Desempregados. Registro mensal de admissões e demissões de trabalhadores com carteira assinada. Publicado pelo MTE via PDET. |
| RAIS | Relação Anual de Informações Sociais. Declaração anual das empresas com dados de todos os vínculos empregatícios do ano anterior. |
| CNAE | Classificação Nacional de Atividades Econômicas. Código de 7 dígitos que identifica o setor de atividade de um CNPJ. |
| CBO | Classificação Brasileira de Ocupações. Código de 6 dígitos que identifica a ocupação do trabalhador admitido/desligado no CAGED. |
| DataJud | Base Nacional de Dados do Poder Judiciário (CNJ). API que fornece acesso a processos judiciais de todos os tribunais brasileiros. |
| TimescaleDB | Extensão open-source do PostgreSQL otimizada para dados de séries temporais com compressão automática e funções de janela temporal. |
| dbt | Data Build Tool. Framework para modelagem, documentação e teste de transformações SQL no data warehouse. |
| MRR | Monthly Recurring Revenue. Receita recorrente mensal de contratos de assinatura. |
| SSR | Server-Side Rendering. Páginas geradas no servidor a cada requisição, favorecendo SEO e tempo de carregamento inicial. |
| SSG | Static Site Generation. Páginas geradas em build time, servidas como HTML estático (máxima performance). |

## **12.2 Referências**

* PDET / MTE — ftp.mtps.gov.br (CAGED, RAIS, CNAE, CBO)

* Receita Federal — dadosabertos.rfb.gov.br (CNPJ, QSA, Situação Cadastral)

* DataJud / CNJ — datajud.cnj.jus.br (processos judiciais)

* Portal da Transparência — portaldatransparencia.gov.br (autuações MTE, FGTS)

* FastAPI Docs — fastapi.tiangolo.com

* Next.js Docs — nextjs.org/docs

* dbt Docs — docs.getdbt.com

* TimescaleDB Docs — docs.timescale.com

* Prefect Docs — docs.prefect.io