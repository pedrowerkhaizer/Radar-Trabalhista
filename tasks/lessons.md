# Lições Aprendidas — Radar Trabalhista

## Formato
Cada lição tem: **contexto** → **erro/padrão** → **regra para evitar no futuro**

---

## Session 001 — 2026-03-01

### L001: Linear como fonte de verdade do projeto
**Contexto**: Iniciamos o projeto com setup de Linear + GitHub + estrutura de repositório.
**Padrão**: Todo trabalho de dev começa como issue no Linear, com ID referenciado nos commits.
**Regra**: Nunca iniciar implementação sem issue Linear correspondente. Branch: `feature/PW-{id}-{slug}`.

### L002: PM gate antes de criar issue
**Contexto**: Coordenação de agentes de IA exige filtro de escopo antes de qualquer implementação.
**Padrão**: Avaliar se feature está no doc técnico antes de criar issue.
**Regra**: Features não mapeadas no doc técnico → recusar com justificativa, não implementar silenciosamente.

### L003: Scaffolding antes de implementação
**Contexto**: Criamos toda a estrutura de pastas e arquivos stub antes de implementar.
**Padrão**: Stubs com `raise NotImplementedError("PW-XX: ...")` marcam claramente o que falta.
**Regra**: Sempre criar stub com referência à issue Linear, nunca arquivo vazio.
