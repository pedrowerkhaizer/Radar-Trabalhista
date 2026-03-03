"""
Seed das tabelas de referência (ref_municipio, ref_cnae, ref_cbo) via APIs públicas.

Fontes:
  - ref_municipio: IBGE servicodados API
  - ref_cnae: IBGE CNAE 2.0 API
  - ref_cbo: embutido (seed estático das grandes famílias CBO)

Uso:
    cd etl
    uv run python seed_refs.py                  # tudo
    uv run python seed_refs.py --only=municipio # só municípios
    uv run python seed_refs.py --only=cnae      # só CNAE
"""

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    load_dotenv(_env_file)

import httpx  # noqa: E402
import psycopg  # noqa: E402


# ──────────────────────────────────────────────
# Conexão
# ──────────────────────────────────────────────

def _get_db_dsn() -> str:
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


# ──────────────────────────────────────────────
# ref_municipio — IBGE servicodados
# ──────────────────────────────────────────────

_UF_NOMES: dict[str, str] = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá",
    "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
    "GO": "Goiás", "MA": "Maranhão", "MG": "Minas Gerais", "MS": "Mato Grosso do Sul",
    "MT": "Mato Grosso", "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco",
    "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RO": "Rondônia", "RR": "Roraima", "RS": "Rio Grande do Sul", "SC": "Santa Catarina",
    "SE": "Sergipe", "SP": "São Paulo", "TO": "Tocantins",
}


def seed_municipios(conn: psycopg.Connection) -> int:
    print("[seed] Buscando municípios do IBGE...")
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome"
    with httpx.Client(timeout=60) as client:
        resp = client.get(url)
        resp.raise_for_status()
        data = resp.json()

    rows = []
    for m in data:
        cod = str(m["id"])  # 7 dígitos IBGE
        nome = m["nome"]
        # Alguns municípios (ex: Boa Esperança do Norte/MT) não têm microrregiao
        if m.get("microrregiao"):
            uf_sigla = m["microrregiao"]["mesorregiao"]["UF"]["sigla"]
        else:
            uf_sigla = m["regiao-imediata"]["regiao-intermediaria"]["UF"]["sigla"]
        nome_uf = _UF_NOMES.get(uf_sigla, uf_sigla)
        rows.append((cod, nome, uf_sigla, nome_uf))

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO ref_municipio (cod_municipio, nome, uf, nome_uf)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (cod_municipio) DO UPDATE SET
                nome = EXCLUDED.nome,
                uf = EXCLUDED.uf,
                nome_uf = EXCLUDED.nome_uf
            """,
            rows,
        )
    conn.commit()
    print(f"[seed] ref_municipio: {len(rows):,} municípios carregados.")
    return len(rows)


# ──────────────────────────────────────────────
# ref_cnae — IBGE CNAE 2.0
# ──────────────────────────────────────────────

def seed_cnae(conn: psycopg.Connection) -> int:
    print("[seed] Buscando CNAE do IBGE...")
    url = "https://servicodados.ibge.gov.br/api/v2/cnae/subclasses"
    with httpx.Client(timeout=60) as client:
        resp = client.get(url)
        resp.raise_for_status()
        data = resp.json()

    rows = []
    for item in data:
        cnae7 = str(item["id"]).replace("-", "").replace("/", "").replace(".", "")
        # Normaliza para 7 chars (IBGE retorna com pontuação)
        cnae7_clean = "".join(c for c in str(item["id"]) if c.isdigit())
        cnae7_padded = cnae7_clean.ljust(7, "0")[:7]
        cnae2 = cnae7_padded[:2]
        descricao = item["descricao"]
        secao = item.get("classe", {}).get("grupo", {}).get("divisao", {}).get("secao", {}).get("descricao", "")
        rows.append((cnae7_padded, cnae2, descricao, secao))

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO ref_cnae (cnae7, cnae2, descricao, secao)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (cnae7) DO UPDATE SET
                cnae2 = EXCLUDED.cnae2,
                descricao = EXCLUDED.descricao,
                secao = EXCLUDED.secao
            """,
            rows,
        )
    conn.commit()
    print(f"[seed] ref_cnae: {len(rows):,} subclasses carregadas.")
    return len(rows)


# ──────────────────────────────────────────────
# ref_cbo — Grandes grupos (seed estático)
# ──────────────────────────────────────────────

# Grandes grupos CBO 2002 (nível família — cbo6 = primeiro 4 dígitos + "00")
# Fonte: http://www.mtecbo.gov.br/cbosite/pages/saibaMais.jsf
_CBO_FAMILIAS: list[tuple[str, str, str]] = [
    ("010105", "Oficial General do Exército", "Forças Armadas"),
    ("010110", "Oficial General da Aeronáutica", "Forças Armadas"),
    ("010115", "Oficial General da Marinha", "Forças Armadas"),
    ("111105", "Senador", "Membros do Poder Legislativo"),
    ("111110", "Deputado Federal", "Membros do Poder Legislativo"),
    ("111115", "Deputado Estadual e Distrital", "Membros do Poder Legislativo"),
    ("111120", "Vereador", "Membros do Poder Legislativo"),
    ("111205", "Presidente da República", "Chefes do Poder Executivo"),
    ("111210", "Vice-Presidente da República", "Chefes do Poder Executivo"),
    ("111215", "Governador de Estado", "Chefes do Poder Executivo"),
    ("111220", "Prefeito", "Chefes do Poder Executivo"),
    ("121005", "Diretor Geral de Empresa e Organizações", "Diretores"),
    ("121010", "Diretor de Produção e Operações", "Diretores"),
    ("121015", "Diretor Administrativo", "Diretores"),
    ("121020", "Diretor Financeiro", "Diretores"),
    ("121025", "Diretor de Recursos Humanos", "Diretores"),
    ("121030", "Diretor Comercial", "Diretores"),
    ("122105", "Gerente de Produção", "Gerentes"),
    ("122110", "Gerente de Operações", "Gerentes"),
    ("131105", "Gerente de Projetos de Tecnologia da Informação", "Gerentes de TI"),
    ("141205", "Gerente de Serviços de Saúde", "Gerentes de Saúde"),
    ("211105", "Físico", "Ciências Físicas"),
    ("211110", "Astrônomo", "Ciências Físicas"),
    ("212205", "Analista de Sistemas", "Informática"),
    ("212210", "Analista de Suporte Computacional", "Informática"),
    ("212310", "Administrador de Banco de Dados", "Informática"),
    ("212320", "Administrador de Redes", "Informática"),
    ("213105", "Químico", "Ciências Químicas"),
    ("214105", "Engenheiro Civil", "Engenharia"),
    ("214110", "Engenheiro Estrutural", "Engenharia"),
    ("214205", "Engenheiro Eletricista", "Engenharia"),
    ("214305", "Engenheiro Mecânico", "Engenharia"),
    ("214405", "Engenheiro Químico", "Engenharia"),
    ("214905", "Engenheiro de Software", "Engenharia de Software"),
    ("214910", "Engenheiro de Dados", "Engenharia de Software"),
    ("221105", "Médico Clínico", "Medicina"),
    ("221110", "Médico Cirurgião", "Medicina"),
    ("222105", "Enfermeiro", "Enfermagem"),
    ("222110", "Enfermeiro de Centro Cirúrgico", "Enfermagem"),
    ("223105", "Fisioterapeuta", "Fisioterapia"),
    ("223205", "Fonoaudiólogo", "Fonoaudiologia"),
    ("224105", "Nutricionista", "Nutrição"),
    ("225105", "Farmacêutico", "Farmácia"),
    ("226305", "Psicólogo", "Psicologia"),
    ("231105", "Professor de Educação Infantil", "Educação"),
    ("231205", "Professor do Ensino Fundamental", "Educação"),
    ("231305", "Professor de Ensino Médio", "Educação"),
    ("232105", "Professor Universitário", "Educação Superior"),
    ("241005", "Advogado", "Direito"),
    ("241010", "Advogado Trabalhista", "Direito"),
    ("241015", "Advogado Tributário", "Direito"),
    ("242205", "Auditor Fiscal", "Fiscalização"),
    ("251105", "Administrador", "Administração"),
    ("251205", "Analista de Recursos Humanos", "RH"),
    ("251210", "Analista de Cargos e Salários", "RH"),
    ("251305", "Analista Financeiro", "Finanças"),
    ("251310", "Analista de Contabilidade", "Finanças"),
    ("251315", "Contador", "Contabilidade"),
    ("252105", "Economista", "Economia"),
    ("252205", "Estatístico", "Estatística"),
    ("252305", "Cientista de Dados", "Dados"),
    ("261105", "Jornalista", "Comunicação"),
    ("261205", "Designer Gráfico", "Design"),
    ("261210", "Designer de Produto", "Design"),
    ("261405", "Publicitário", "Publicidade"),
    ("261505", "Arquivista", "Arquivologia"),
    ("261705", "Tradutor", "Tradução"),
    ("262105", "Ator", "Artes"),
    ("262205", "Músico", "Artes"),
    ("311105", "Técnico Químico", "Técnicos"),
    ("311505", "Técnico de Edificações", "Técnicos"),
    ("313105", "Técnico em Eletricidade", "Técnicos"),
    ("313205", "Técnico em Eletrônica", "Técnicos"),
    ("314105", "Técnico Mecânico", "Técnicos"),
    ("317105", "Técnico em Informática", "TI"),
    ("317110", "Técnico em Suporte de TI", "TI"),
    ("321105", "Técnico de Enfermagem", "Saúde"),
    ("322205", "Técnico em Farmácia", "Saúde"),
    ("322210", "Auxiliar de Farmácia", "Saúde"),
    ("341105", "Piloto de Aviação Civil", "Transporte"),
    ("342105", "Marinheiro", "Transporte Marítimo"),
    ("342205", "Maquinista Ferroviário", "Transporte"),
    ("342305", "Motorista de Ônibus", "Transporte"),
    ("342310", "Motorista de Caminhão", "Transporte"),
    ("342315", "Motorista de Táxi e Aplicativo", "Transporte"),
    ("351105", "Corretor de Imóveis", "Comércio"),
    ("351205", "Corretor de Seguros", "Seguros"),
    ("351305", "Corretor de Valores", "Mercado Financeiro"),
    ("351605", "Técnico Contábil", "Contabilidade"),
    ("354205", "Agente Fiscal", "Fiscalização"),
    ("371105", "Técnico de Segurança do Trabalho", "Segurança"),
    ("374105", "Técnico de Rádio e TV", "Comunicação"),
    ("375105", "Técnico em Nutrição", "Saúde"),
    ("391105", "Técnico Naval", "Construção Naval"),
    ("410105", "Supervisor Administrativo", "Administrativo"),
    ("411005", "Assistente Administrativo", "Administrativo"),
    ("411010", "Auxiliar Administrativo", "Administrativo"),
    ("412105", "Recepcionista", "Administrativo"),
    ("412110", "Operador de Telemarketing", "Administrativo"),
    ("413105", "Escriturário de Banco", "Finanças"),
    ("413110", "Caixa de Banco", "Finanças"),
    ("414105", "Almoxarife", "Logística"),
    ("414110", "Operador de Estoque", "Logística"),
    ("415105", "Carteiro", "Correios"),
    ("415205", "Operador de Digitação", "Administrativo"),
    ("420105", "Supervisor de Vendas", "Vendas"),
    ("421105", "Atendente de Agência", "Vendas"),
    ("421205", "Caixa de Comércio", "Vendas"),
    ("422105", "Operador de Call Center", "Atendimento"),
    ("422110", "Atendente de SAC", "Atendimento"),
    ("424105", "Agente de Viagens", "Turismo"),
    ("510105", "Supervisor de Serviços", "Serviços"),
    ("511105", "Comissário de Bordo", "Transporte"),
    ("511205", "Guia de Turismo", "Turismo"),
    ("512105", "Cozinheiro", "Alimentação"),
    ("512110", "Garçom", "Alimentação"),
    ("512115", "Barman", "Alimentação"),
    ("513405", "Cabeleireiro", "Estética"),
    ("514105", "Vigilante", "Segurança"),
    ("514110", "Porteiro", "Segurança"),
    ("514305", "Gari", "Limpeza"),
    ("515105", "Agente Comunitário de Saúde", "Saúde"),
    ("515120", "Auxiliar de Enfermagem", "Saúde"),
    ("516110", "Auxiliar de Serviços Gerais", "Serviços"),
    ("516305", "Doméstica", "Serviços Domésticos"),
    ("519905", "Operador de Caixa", "Comércio"),
    ("521105", "Vendedor Interno", "Vendas"),
    ("521110", "Vendedor Externo", "Vendas"),
    ("521115", "Promotor de Vendas", "Vendas"),
    ("521120", "Representante Comercial", "Vendas"),
    ("524205", "Repositor de Mercadorias", "Logística"),
    ("611005", "Produtor Agrícola", "Agropecuária"),
    ("611105", "Trabalhador Agrícola", "Agropecuária"),
    ("612005", "Pecuarista", "Agropecuária"),
    ("621005", "Trabalhador Volante Agrícola", "Agropecuária"),
    ("631005", "Trabalhador Florestal", "Silvicultura"),
    ("641005", "Pescador", "Pesca"),
    ("711105", "Operador de Mineração", "Mineração"),
    ("711205", "Blaster", "Mineração"),
    ("712105", "Pedreiro", "Construção"),
    ("712110", "Mestre de Obras", "Construção"),
    ("712205", "Azulejista", "Construção"),
    ("712305", "Carpinteiro", "Construção"),
    ("712310", "Marceneiro", "Móveis"),
    ("712315", "Montador de Móveis", "Móveis"),
    ("712405", "Eletricista de Instalações", "Eletricidade"),
    ("712410", "Instalador de Redes", "Telecomunicações"),
    ("712505", "Bombeiro Hidráulico", "Construção"),
    ("712605", "Pintor de Obras", "Construção"),
    ("715505", "Soldador", "Metalurgia"),
    ("716205", "Encanador", "Construção"),
    ("717005", "Ajudante de Obras", "Construção"),
    ("721105", "Operador de Fundição", "Metalurgia"),
    ("722105", "Ferreiro", "Metalurgia"),
    ("723205", "Torneiro Mecânico", "Metalurgia"),
    ("731105", "Operador de Máquinas Gráficas", "Gráfica"),
    ("741105", "Eletricista de Manutenção", "Eletricidade"),
    ("742105", "Técnico em Refrigeração", "Refrigeração"),
    ("750105", "Joalheiro", "Artesanato"),
    ("760105", "Operador Têxtil", "Têxtil"),
    ("764105", "Costureiro", "Têxtil"),
    ("765105", "Sapateiro", "Calçados"),
    ("771105", "Marceneiro", "Móveis"),
    ("782105", "Motorista de Veículo Pesado", "Transporte"),
    ("782110", "Operador de Empilhadeira", "Logística"),
    ("783205", "Auxiliar de Logística", "Logística"),
    ("784105", "Estivador", "Logística"),
    ("791105", "Operador de Limpeza Industrial", "Indústria"),
    ("811105", "Operador de Usina", "Energia"),
    ("821105", "Operador de Linha de Produção", "Indústria"),
    ("821205", "Operador de Montagem Industrial", "Indústria"),
    ("831105", "Operador de Colheita", "Agropecuária"),
    ("840105", "Trabalhador em Indústria de Alimentos", "Alimentação"),
    ("848305", "Trabalhador em Indústria Química", "Química"),
    ("862105", "Operador de Caldeira", "Indústria"),
    ("910105", "Mecânico de Manutenção", "Manutenção"),
    ("910205", "Mecânico de Automóvel", "Manutenção"),
    ("910210", "Eletricista Automotivo", "Manutenção"),
    ("950105", "Instalador de Sistemas Elétricos", "Eletricidade"),
    ("991305", "Trabalhador em Serviços de Conservação", "Serviços"),
]


def seed_cbo(conn: psycopg.Connection) -> int:
    print(f"[seed] Carregando {len(_CBO_FAMILIAS)} famílias CBO...")
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO ref_cbo (cbo6, descricao, grupo)
            VALUES (%s, %s, %s)
            ON CONFLICT (cbo6) DO UPDATE SET
                descricao = EXCLUDED.descricao,
                grupo = EXCLUDED.grupo
            """,
            _CBO_FAMILIAS,
        )
    conn.commit()
    print(f"[seed] ref_cbo: {len(_CBO_FAMILIAS):,} registros carregados.")
    return len(_CBO_FAMILIAS)


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main() -> None:
    flags = {a.lstrip("-").split("=")[0]: a.split("=")[1] if "=" in a else True
             for a in sys.argv[1:] if a.startswith("--")}
    only = flags.get("only")

    t0 = time.monotonic()
    dsn = _get_db_dsn()

    with psycopg.connect(dsn) as conn:
        if only in (None, "municipio"):
            seed_municipios(conn)

        if only in (None, "cnae"):
            seed_cnae(conn)

        if only in (None, "cbo"):
            seed_cbo(conn)

    print(f"\n[seed] Concluído em {time.monotonic() - t0:.1f}s")


if __name__ == "__main__":
    main()
