"""
utils/catalogo.py
O plano de marketing dentro do app: o catálogo de ofertas que a operadora pode fazer.

O marketing liga e desliga cada oferta, escreve a fala e define até quando vale e para quais segmentos. A escada de
ofertas do Atendimento só usa o que está ativo, vigente e liberado para o segmento do cliente. Nesta versão, o catálogo
fica na sessão do app (volta ao padrão ao recarregar); em produção, vira uma tabela no Unity Catalog mantida pelo marketing.
"""

from datetime import date

import pandas as pd
import streamlit as st

from motor.modelo import ACOES

SEGMENTOS = ["S1", "S2", "S3", "S4", "S5"]
VIGENCIA_PADRAO = date(2026, 12, 31)


def padrao() -> pd.DataFrame:
    return pd.DataFrame([{"codigo": k, "Oferta": d["rotulo"], "Ativa": True, "Fala para a operadora": d["fala"],
                          "Válida até": VIGENCIA_PADRAO, "Segmentos": ", ".join(SEGMENTOS)} for k, d in ACOES.items()])


def catalogo() -> pd.DataFrame:
    if "catalogo" not in st.session_state:
        st.session_state["catalogo"] = padrao()
    return st.session_state["catalogo"]


def salvar(df: pd.DataFrame):
    st.session_state["catalogo"] = df.reset_index(drop=True)


def _segmentos(texto) -> set:
    return {s.strip().upper() for s in str(texto or "").replace(";", ",").split(",") if s.strip()}


def liberadas(segmento: str | None = None, hoje: date | None = None) -> set:
    """Códigos das ofertas ativas, vigentes e liberadas para o segmento."""
    hoje = hoje or date.today()
    c = catalogo()
    ok = set()
    for _, r in c.iterrows():
        validade = pd.to_datetime(r["Válida até"], errors="coerce")
        vigente = pd.isna(validade) or validade.date() >= hoje
        segs = _segmentos(r["Segmentos"])
        seg_ok = segmento is None or not segs or str(segmento).upper() in segs
        if bool(r["Ativa"]) and vigente and seg_ok:
            ok.add(r["codigo"])
    return ok


def fala(codigo: str) -> str:
    c = catalogo().set_index("codigo")
    return str(c.loc[codigo, "Fala para a operadora"]) if codigo in c.index else ACOES[codigo]["fala"]


def filtrar(ofertas: pd.DataFrame, segmento: str | None = None) -> pd.DataFrame:
    """Só as ofertas cujas ações estão todas no catálogo liberado (para a escada do cliente ou para a fila inteira)."""
    if ofertas.empty:
        return ofertas
    ok = liberadas(segmento)
    return ofertas[ofertas["acoes"].apply(lambda a: all(x in ok for x in a))]
