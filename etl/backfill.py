"""
Script de backfill manual do CAGED — carrega meses históricos no Supabase.

Uso:
    cd etl
    uv run python backfill.py                    # últimos 3 meses
    uv run python backfill.py 2024-01 2024-12    # intervalo específico

Requisitos:
    - ../.env com POSTGRES_HOST, POSTGRES_PASSWORD etc. (Supabase)
    - Sem necessidade de servidor Prefect rodando
"""

import sys
from datetime import date, timedelta
from pathlib import Path

# Carrega .env do diretório pai automaticamente
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_file)
    print(f"[backfill] .env carregado de {_env_file}")
else:
    print(f"[backfill] Aviso: .env não encontrado em {_env_file}")


def _default_competencias(n: int = 3) -> list[str]:
    """Retorna os últimos N meses no formato YYYY-MM."""
    today = date.today()
    result = []
    for i in range(n, 0, -1):
        d = (today.replace(day=1) - timedelta(days=1)) - timedelta(days=30 * (i - 1))
        result.append(d.strftime("%Y-%m"))
    return result


def _parse_competencias(args: list[str]) -> list[str]:
    """Interpreta argumentos como lista ou intervalo de competências YYYY-MM."""
    if len(args) == 1:
        return args
    if len(args) == 2:
        # Intervalo: gera todos os meses entre args[0] e args[1]
        start_y, start_m = map(int, args[0].split("-"))
        end_y, end_m = map(int, args[1].split("-"))
        result = []
        y, m = start_y, start_m
        while (y, m) <= (end_y, end_m):
            result.append(f"{y:04d}-{m:02d}")
            m += 1
            if m > 12:
                m = 1
                y += 1
        return result
    return args


def main() -> None:
    # Import após carregar .env para garantir variáveis disponíveis
    from flows.caged_flow import caged_etl_flow  # noqa: PLC0415

    args = sys.argv[1:]
    competencias = _parse_competencias(args) if args else _default_competencias(3)

    print(f"\n[backfill] Competências a processar: {competencias}\n")

    resultados = []
    for comp in competencias:
        print(f"[backfill] ▶ Iniciando {comp} ...")
        try:
            stats = caged_etl_flow(competencia=comp)
            resultados.append({"competencia": comp, "status": "ok", **stats})
            print(f"[backfill] ✓ {comp}: {stats['linhas']:,} linhas em {stats['duracao_s']}s")
        except Exception as exc:
            resultados.append({"competencia": comp, "status": "erro", "erro": str(exc)})
            print(f"[backfill] ✗ {comp}: ERRO — {exc}")

    print("\n[backfill] Resumo:")
    for r in resultados:
        status = "✓" if r["status"] == "ok" else "✗"
        linhas = f"{r.get('linhas', 0):,} linhas" if r["status"] == "ok" else r.get("erro", "")
        print(f"  {status} {r['competencia']} — {linhas}")


if __name__ == "__main__":
    main()
