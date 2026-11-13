"""
utils/dados.py
Leitura das tabelas do monitoramento.

Duas fontes, na ordem:
1. Unity Catalog, por um SQL Warehouse (quando o app roda como Databricks App com o recurso "sql-warehouse");
2. os CSV da pasta dados/, que o notebook 09 grava (para rodar localmente ou sem warehouse).
"""

import os
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent.parent
PASTA_DADOS = BASE_DIR / "dados"
FQ = os.getenv("TS_SCHEMA", "workspace.terra_signal")
WAREHOUSE = os.getenv("DATABRICKS_WAREHOUSE_ID", "")

TABELAS = ["gold_churn_monitoramento", "gold_churn_monitoramento_distribuicao", "gold_churn_fila_retencao",
           "gold_churn_modelo_info", "gold_churn_segmentos_perfil"]


def _ler_sql(tabela: str) -> pd.DataFrame:
    from databricks import sql
    from databricks.sdk.core import Config

    cfg = Config()          # no Databricks App, as credenciais vêm do próprio app
    with sql.connect(server_hostname=cfg.host, http_path=f"/sql/1.0/warehouses/{WAREHOUSE}",
                     credentials_provider=lambda: cfg.authenticate) as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {FQ}.{tabela}")
            return cursor.fetchall_arrow().to_pandas()


def _ler_csv(tabela: str) -> pd.DataFrame:
    caminho = PASTA_DADOS / f"{tabela}.csv"
    if not caminho.exists():
        raise FileNotFoundError(f"{caminho} não existe: rode o notebook 09 (seção 5)")
    return pd.read_csv(caminho)


@st.cache_data(ttl=600, show_spinner="Carregando os dados do monitoramento…")
def ler(tabela: str) -> tuple[pd.DataFrame, str]:
    """Devolve (tabela, fonte). Tenta o SQL Warehouse e, se não houver, os CSV."""
    if WAREHOUSE:
        try:
            return _ler_sql(tabela), f"Unity Catalog · {FQ}.{tabela}"
        except Exception as erro:          # sem permissão ou sem warehouse: cai para o CSV
            st.session_state.setdefault("avisos", []).append(f"{tabela}: SQL indisponível ({type(erro).__name__}); usando CSV")
    return _ler_csv(tabela), f"CSV · dados/{tabela}.csv"


def carregar_tudo() -> dict:
    """Todas as tabelas do app, já com os tipos acertados."""
    d = {}
    for t in TABELAS:
        df, fonte = ler(t)
        d[t] = df
        d[f"{t}__fonte"] = fonte
    m = d["gold_churn_monitoramento"]
    for c in ["valor", "referencia", "limite_atencao", "limite_alerta"]:
        m[c] = pd.to_numeric(m[c], errors="coerce")
    dist = d["gold_churn_monitoramento_distribuicao"]
    for c in ["pct_referencia", "pct_lote", "ordem"]:
        dist[c] = pd.to_numeric(dist[c], errors="coerce")
    return d


@st.cache_resource(show_spinner="Carregando o motor de atendimento…")
def carregar_motor():
    """O motor do notebook 10: parâmetros do modelo oficial e tabela de preço (dados/modelo_motor.json)."""
    from motor import Motor
    caminho = PASTA_DADOS / "modelo_motor.json"
    if not caminho.exists():
        raise FileNotFoundError(f"{caminho} não existe: rode o notebook 10 (seção 5)")
    return Motor.carregar(str(caminho))


@st.cache_data(ttl=600, show_spinner="Carregando a carteira…")
def carregar_clientes() -> pd.DataFrame:
    """A ficha de cada cliente da carteira, com nota, segmento e escada de ofertas (dados/clientes_atendimento.csv)."""
    caminho = PASTA_DADOS / "clientes_atendimento.csv"
    if not caminho.exists():
        raise FileNotFoundError(f"{caminho} não existe: rode o notebook 10 (seção 5)")
    return pd.read_csv(caminho).sort_values("Probabilidade_Churn", ascending=False).reset_index(drop=True)


@st.cache_data(ttl=600)
def carregar_ganho() -> pd.DataFrame:
    """Taxa real de churn por decil no teste e curva de ganho (dados/ganho_teste.csv, notebook 10, 5.2)."""
    caminho = PASTA_DADOS / "ganho_teste.csv"
    if not caminho.exists():
        raise FileNotFoundError(f"{caminho} não existe: rode o notebook 10 (seção 5.2)")
    return pd.read_csv(caminho)


def lotes(monit: pd.DataFrame) -> list:
    """Lotes em ordem de execução, o mais recente primeiro; o lote simulado por último."""
    ordem = (monit.groupby("lote")["data_execucao"].max().sort_values(ascending=False).index.tolist())
    reais = [l for l in ordem if not str(l).startswith("simulacao")]
    simulados = [l for l in ordem if str(l).startswith("simulacao")]
    return reais + simulados


def nome_lote(lote: str) -> str:
    """Nome para mostrar: carteira_2026_11 → Carteira 11/2026; simulacao_... → Lote simulado (...)."""
    l = str(lote)
    if l.startswith("simulacao"):
        resto = l.replace("simulacao_", "").replace("_", " ")
        return f"Lote simulado ({resto})" if resto else "Lote simulado"
    partes = l.split("_")
    if len(partes) == 3 and partes[0] == "carteira" and partes[1].isdigit():
        return f"Carteira {partes[2]}/{partes[1]}"
    return l


@st.cache_data(ttl=600)
def carregar_relatos() -> pd.DataFrame:
    """Último relato de cada cliente da carteira: saída declarada, tom, motivos, abordagem e receptividade
    (dados/relatos_inferencia.csv, notebook 10, 5.3). Sem o arquivo, devolve vazio e o app segue sem o relato."""
    caminho = PASTA_DADOS / "relatos_inferencia.csv"
    if not caminho.exists():
        return pd.DataFrame(columns=["customerID", "relato", "decidiu_sair", "tom", "motivos_citados", "abordagem",
                                     "receptividade"])
    return pd.read_csv(caminho, keep_default_na=False)
