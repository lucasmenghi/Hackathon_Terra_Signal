"""
utils/pagina.py
Abertura padrão de cada página: configuração, tema, header, dados e o filtro de lote na barra lateral.
"""

import streamlit as st

from config.theme import QUADRANTES, SEGMENTOS, aplicar_tema, logo_base64, page_header
from utils.dados import carregar_tudo, lotes, nome_lote


def abrir_pagina(titulo: str, subtitulo: str, imagem: str = "", com_lote: bool = True, carregar: bool = True):
    st.set_page_config(page_title=f"{titulo} · Central de retenção Terra Signal", layout="wide",
                       initial_sidebar_state="expanded")
    aplicar_tema()
    sidebar_header()
    page_header(titulo, subtitulo, imagem)
    if not carregar:
        return {}, None
    try:
        dados = carregar_tudo()
    except FileNotFoundError as erro:
        st.error(f"Sem dados do monitoramento: {erro}")
        st.stop()
    lote = None
    if com_lote:
        opcoes = lotes(dados["gold_churn_monitoramento"])
        padrao = st.session_state.get("lote", opcoes[0])
        lote = st.sidebar.selectbox("Lote", opcoes, index=opcoes.index(padrao) if padrao in opcoes else 0,
                                    format_func=nome_lote, help="Carteira pontuada pelo modelo. O lote simulado "
                                    "testa se o monitor acende quando a carteira muda (notebook 09, seção 3).")
        st.session_state["lote"] = lote
    for aviso in st.session_state.pop("avisos", []):
        st.sidebar.caption(aviso)
    return dados, lote


def sidebar_header():
    with st.sidebar:
        src = logo_base64()
        if src:
            st.markdown(f'<div style="padding:0.6rem 0.5rem 0.2rem;"><img src="{src}" style="max-width:150px;width:100%;" /></div>',
                        unsafe_allow_html=True)
        st.markdown('<p style="font-size:13px;color:#4B5563;padding:0 0.5rem;">Central de retenção<br>'
                    'Terra Signal · Grupo 4</p>', unsafe_allow_html=True)
        with st.expander("Legenda: segmentos, decis e quadrantes"):
            st.markdown("**Segmentos** (tipos de cliente, notebook 07)\n\n" + "\n".join(
                f"- **{k} · {v[0]}:** {v[1]}" for k, v in SEGMENTOS.items()))
            st.markdown("**Decis de risco**\n\n- **D1:** os 10% de maior risco da carteira\n- **D10:** os 10% de menor risco\n"
                        "- **Risco Alto:** D1 e D2 · **Médio:** D3 a D5 · **Baixo:** D6 a D10")
            st.markdown("**Quadrantes** (risco × mensalidade)\n\n" + "\n".join(f"- **{k}:** {v}" for k, v in QUADRANTES.items()))
            st.markdown("**Nota de risco:** probabilidade do modelo, de 0 a 1; acima de 0,50, o cliente entra na fila. "
                        "Serve para ordenar, não é a chance exata.")
        st.divider()
