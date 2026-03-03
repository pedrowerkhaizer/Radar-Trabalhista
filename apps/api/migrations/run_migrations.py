"""
Aplica todas as migrations SQL em ordem, de forma idempotente.

Uso:
    cd apps/api
    uv run python migrations/run_migrations.py

    # Ver o que seria executado sem aplicar:
    uv run python migrations/run_migrations.py --dry-run

Todas as migrations usam IF NOT EXISTS — seguro rodar múltiplas vezes.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Carrega .env da raiz do projeto
_env_file = Path(__file__).parent.parent.parent / ".env"
if _env_file.exists():
    load_dotenv(_env_file)

import psycopg  # noqa: E402


def _get_dsn() -> str:
    host = os.getenv("POSTGRES_HOST", "localhost")
    sslmode = os.getenv(
        "POSTGRES_SSLMODE",
        "require" if "supabase.co" in host else "prefer",
    )
    return (
        f"host={host} "
        f"port={os.getenv('POSTGRES_PORT', '5432')} "
        f"dbname={os.getenv('POSTGRES_DB', 'postgres')} "
        f"user={os.getenv('POSTGRES_USER', 'postgres')} "
        f"password={os.getenv('POSTGRES_PASSWORD', '')} "
        f"sslmode={sslmode}"
    )


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    migrations_dir = Path(__file__).parent
    sql_files = sorted(migrations_dir.glob("*.sql"))

    if not sql_files:
        print("Nenhuma migration SQL encontrada.")
        return

    print(f"[migrations] Encontradas {len(sql_files)} migration(s):")
    for f in sql_files:
        print(f"  {f.name}")

    if dry_run:
        print("\n[migrations] --dry-run: nenhuma alteração aplicada.")
        return

    dsn = _get_dsn()
    print(f"\n[migrations] Conectando em {os.getenv('POSTGRES_HOST', 'localhost')}...")

    try:
        conn = psycopg.connect(dsn)
    except Exception as exc:
        print(f"[migrations] ✗ Falha na conexão: {exc}")
        sys.exit(1)

    with conn:
        for sql_file in sql_files:
            print(f"\n[migrations] ▶ Aplicando {sql_file.name} ...")
            sql = sql_file.read_text(encoding="utf-8")
            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                print(f"[migrations] ✓ {sql_file.name} aplicada com sucesso.")
            except Exception as exc:
                print(f"[migrations] ✗ Erro em {sql_file.name}: {exc}")
                sys.exit(1)

    conn.close()
    print("\n[migrations] Todas as migrations aplicadas com sucesso!")


if __name__ == "__main__":
    main()
