"""Página 7 — Pergunte aos dados: o Genie (Terra Signal · Retenção) dentro do app.

O app conversa com o espaço do Genie pela Conversation API (databricks-sdk). O ID do espaço vem do recurso "genie-space"
do app (variável GENIE_SPACE_ID, no app.yaml). O service principal do app precisa de acesso ao espaço (recurso) e de
SELECT nas tabelas de workspace.terra_signal (ver README).
"""

import os

import pandas as pd
import streamlit as st

from config.theme import COR, DESTAQUE, QUADRANTES, SEGMENTOS, TEXTO_2, explicar, secao_titulo
from utils.pagina import abrir_pagina

abrir_pagina("Pergunte aos dados", "Perguntas em português sobre a carteira, respondidas pelo Genie", imagem="ilustracao_genie.png",
             com_lote=False, carregar=False)

SPACE_ID = os.getenv("GENIE_SPACE_ID", "").strip()
SUGESTOES = [
    "Quantos clientes estão previstos para sair, por segmento?",
    "Qual a receita mensal dos clientes com sinal de saída em cada segmento?",
    "Quais os 20 clientes de maior risco no quadrante Salvar já?",
    "Qual a oferta principal mais comum na fila de retenção?",
    "Algum indicador do monitoramento está em alerta na carteira atual?",
]

if not SPACE_ID:
    st.info("O Genie ainda não está ligado a este app. Na página do app no Databricks: Edit → App resources → Add resource → "
            "Genie space (Terra Signal · Retenção), permissão Can run, chave genie-space. Depois, Deploy.")
    st.stop()


@st.cache_resource
def cliente():
    from databricks.sdk import WorkspaceClient
    return WorkspaceClient()


def resultado_da_consulta(w, conversa_id: str, mensagem_id: str, anexo) -> pd.DataFrame | None:
    """Tabela da consulta que o Genie gerou (pela execução do SQL ou pelo resultado do anexo)."""
    resp = None
    try:
        resp = w.genie.get_message_attachment_query_result(SPACE_ID, conversa_id, mensagem_id, anexo.attachment_id).statement_response
    except Exception:
        stmt = getattr(anexo.query, "statement_id", None)
        if stmt:
            resp = w.statement_execution.get_statement(stmt)
    if resp is None or resp.result is None or resp.manifest is None:
        return None
    colunas = [c.name for c in resp.manifest.schema.columns]
    df = pd.DataFrame(resp.result.data_array or [], columns=colunas)
    for c in df.columns:
        convertido = pd.to_numeric(df[c], errors="coerce")
        if convertido.notna().sum() == df[c].notna().sum() and df[c].notna().any():
            df[c] = convertido
    return df


def perguntar(texto: str) -> dict:
    w = cliente()
    conversa = st.session_state.get("genie_conversa")
    if conversa:
        msg = w.genie.create_message_and_wait(SPACE_ID, conversa, texto)
    else:
        msg = w.genie.start_conversation_and_wait(SPACE_ID, texto)
        st.session_state["genie_conversa"] = msg.conversation_id
    resposta = {"papel": "genie", "texto": [], "tabelas": [], "sql": [], "descricao": []}
    for anexo in msg.attachments or []:
        if getattr(anexo, "text", None) and anexo.text.content:
            resposta["texto"].append(anexo.text.content)
        if getattr(anexo, "query", None):
            if anexo.query.description:
                resposta["descricao"].append(anexo.query.description)
            if anexo.query.query:
                resposta["sql"].append(anexo.query.query)
            df = resultado_da_consulta(w, msg.conversation_id, msg.id, anexo)
            if df is not None:
                resposta["tabelas"].append(df)
    if not resposta["texto"] and not resposta["tabelas"]:
        resposta["texto"].append("O Genie não trouxe resposta para esta pergunta. Tente reformular.")
    return resposta


def barras(df: pd.DataFrame, cat: str, num: str):
    """Barras horizontais simples, com o valor escrito na ponta (mesmo padrão dos gráficos do app)."""
    import plotly.graph_objects as go
    from config.theme import virg
    d = df.sort_values(num)
    casas = 0 if (d[num] % 1 == 0).all() else 1
    fig = go.Figure(go.Bar(x=d[num], y=d[cat].astype(str), orientation="h", marker_color=COR, width=0.6,
                           text=[virg(v, casas) for v in d[num]], textposition="outside", cliponaxis=False,
                           textfont=dict(size=13, color="#1A1A1A"), hovertemplate="%{y}: %{x}<extra></extra>"))
    fig.update_layout(height=70 + 38 * len(d), margin=dict(l=10, r=60, t=10, b=10), plot_bgcolor="white",
                      paper_bgcolor="white", showlegend=False, separators=",.",
                      font=dict(family="Helvetica Neue, Helvetica, Arial, sans-serif", size=13, color="#1A1A1A"))
    fig.update_xaxes(visible=False, range=[0, float(d[num].max()) * 1.15])
    fig.update_yaxes(automargin=True, tickfont=dict(size=13, color="#1A1A1A"), ticks="")
    return fig


def _md_para_html(texto: str) -> str:
    """Markdown simples do Genie (negrito e listas) em HTML seguro, para caber no balão."""
    import html
    import re
    linhas, saida, em_lista = html.escape(texto).split("\n"), [], False
    for l in linhas:
        l = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", l.strip())
        item = re.match(r"^[-*•]\s+(.*)", l)
        if item:
            if not em_lista:
                saida.append('<ul style="margin:4px 0 4px 18px;padding:0;">')
                em_lista = True
            saida.append(f"<li>{item.group(1)}</li>")
            continue
        if em_lista:
            saida.append("</ul>")
            em_lista = False
        if l:
            saida.append(f'<p style="margin:0 0 6px;">{l}</p>')
    if em_lista:
        saida.append("</ul>")
    return "".join(saida)


def _avatar(letra: str, cor: str) -> str:
    return (f'<div style="width:36px;height:36px;border-radius:50%;background:{cor};color:#fff;font-weight:700;'
            f'display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0;">{letra}</div>')


def _balao(conteudo_html: str, lado: str, hora: str):
    """Balão de conversa: o usuário à direita (azul), o Genie à esquerda (branco com borda)."""
    if lado == "direita":
        st.markdown(f"""
<div style="display:flex;justify-content:flex-end;align-items:flex-end;gap:8px;margin:10px 0;">
  <div style="max-width:70%;background:{COR};color:#fff;padding:10px 14px;border-radius:16px 16px 4px 16px;
              font-size:15px;line-height:1.5;box-shadow:0 1px 2px rgba(0,0,0,0.12);">
    {conteudo_html}
    <div style="text-align:right;font-size:12px;opacity:0.85;margin-top:2px;">{hora}</div>
  </div>
  {_avatar("V", "#174f63")}
</div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div style="display:flex;justify-content:flex-start;align-items:flex-end;gap:8px;margin:10px 0;">
  {_avatar("G", DESTAQUE)}
  <div style="max-width:78%;background:#fff;color:#1A1A1A;padding:10px 14px;border:1px solid #E5E7EB;
              border-radius:16px 16px 16px 4px;font-size:15px;line-height:1.55;box-shadow:0 1px 2px rgba(0,0,0,0.06);">
    <div style="font-size:12.5px;font-weight:700;color:{DESTAQUE};margin-bottom:4px;">Genie · Terra Signal</div>
    {conteudo_html}
    <div style="text-align:right;font-size:12px;color:#4B5563;margin-top:2px;">{hora}</div>
  </div>
</div>""", unsafe_allow_html=True)


def mostrar(item: dict):
    import html
    hora = item.get("hora", "")
    if item["papel"] == "voce":
        _balao(html.escape(item["texto"]), "direita", hora)
        return
    corpo = "".join(_md_para_html(t) for t in item["texto"])
    for d in item.get("descricao", []):
        corpo += f'<p style="margin:6px 0 0;font-size:13px;color:#4B5563;">Consulta: {html.escape(d)}</p>'
    _balao(corpo, "esquerda", hora)
    if item["tabelas"] or item["sql"]:
        _, conteudo, _ = st.columns([0.045, 0.78, 0.175])        # alinhado com o balão do Genie
        with conteudo:
            for df in item["tabelas"]:
                num = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
                cat = [c for c in df.columns if c not in num]
                if len(df) <= 15 and len(num) == 1 and len(cat) == 1 and len(df) > 1:
                    st.plotly_chart(barras(df, cat[0], num[0]), use_container_width=True, theme=None,
                                    config={"displayModeBar": False})
                st.dataframe(df, hide_index=True, use_container_width=True)
            for q in item["sql"]:
                with st.expander("Ver o SQL que o Genie gerou"):
                    st.code(q, language="sql")
    legenda_da_resposta(item)


def legenda_da_resposta(item: dict):
    """Se a resposta cita segmentos (S1 a S5) ou quadrantes, mostra embaixo o que cada um significa."""
    import re
    textos = " ".join(item["texto"]) + " " + " ".join(df.astype(str).to_csv(index=False) for df in item["tabelas"])
    segs = [k for k in SEGMENTOS if re.search(rf"\b{k}\b", textos)]
    quads = [k for k in QUADRANTES if k.lower() in textos.lower()]
    if not segs and not quads:
        return
    partes = [f"<b>{k}</b> = {SEGMENTOS[k][0]}" for k in segs] + [f"<b>{k}</b> = {QUADRANTES[k]}" for k in quads]
    _, conteudo, _ = st.columns([0.045, 0.78, 0.175])
    with conteudo:
        st.markdown(f'<div style="font-size:13px;color:#1A1A1A;background:#F3F6F7;border-radius:8px;padding:6px 10px;'
                    f'line-height:1.7;"><b style="color:#4B5563;">Legenda:</b> {" · ".join(partes)}</div>',
                    unsafe_allow_html=True)


secao_titulo("PERGUNTE", "O que você quer saber da carteira?",
             "O Genie lê as tabelas do modelo, dos segmentos, das ofertas e do monitoramento e responde em português. "
             "Confira sempre o SQL: ele mostra exatamente o que foi contado.")
explicar("""- **Clique numa pergunta pronta** ou escreva a sua no campo de baixo. A conversa continua: dá para perguntar "e a receita?" em seguida.
- **O Genie conhece:** a nota e o decil de cada cliente, os segmentos (S1 a S5) e quadrantes, a escada de ofertas e os indicadores do monitoramento.
- **A resposta traz** o texto, um gráfico quando a tabela é simples, a tabela e o SQL que ele rodou.
- **Confira o SQL** nos números importantes: o Genie é uma IA e pode interpretar uma pergunta de outro jeito.
- **Boas perguntas:** citam o grupo e a medida ("receita mensal dos clientes em risco no S2").""", "Como usar o Genie")
st.session_state.setdefault("genie_historico", [])

escolhida = None
for linha in (SUGESTOES[:3], SUGESTOES[3:]):
    for col, sug in zip(st.columns(3), linha):
        with col:
            if st.button(sug, use_container_width=True):
                escolhida = sug

for item in st.session_state["genie_historico"]:
    mostrar(item)

pergunta = st.chat_input("Escreva sua pergunta…") or escolhida
if pergunta:
    from datetime import datetime
    from zoneinfo import ZoneInfo
    FUSO = ZoneInfo("America/Sao_Paulo")
    agora = datetime.now(FUSO).strftime("%H:%M")
    item_voce = {"papel": "voce", "texto": pergunta, "hora": agora}
    st.session_state["genie_historico"].append(item_voce)
    mostrar(item_voce)
    digitando = st.empty()
    digitando.markdown(f"""
<div style="display:flex;align-items:flex-end;gap:8px;margin:10px 0;">
  {_avatar("G", DESTAQUE)}
  <div style="background:#fff;border:1px solid #E5E7EB;border-radius:16px 16px 16px 4px;padding:10px 14px;font-size:14px;
              color:#4B5563;font-style:italic;">Genie está digitando… consultando os dados</div>
</div>""", unsafe_allow_html=True)
    try:
        resp = perguntar(pergunta)
    except Exception as erro:
        resp = {"papel": "genie", "tabelas": [], "sql": [],
                "texto": [f"Não consegui falar com o Genie ({type(erro).__name__}). Confira se o app tem o recurso "
                          f"genie-space e SELECT em workspace.terra_signal. Detalhe: {str(erro)[:200]}"]}
    digitando.empty()
    resp["hora"] = datetime.now(FUSO).strftime("%H:%M")
    st.session_state["genie_historico"].append(resp)
    mostrar(resp)

if st.session_state["genie_historico"]:
    if st.button("Nova conversa"):
        st.session_state["genie_historico"] = []
        st.session_state.pop("genie_conversa", None)
        st.rerun()
st.caption(f"Espaço do Genie: Terra Signal · Retenção ({SPACE_ID[:8]}…). As respostas são geradas por IA a partir das "
           "tabelas; confira os números importantes no SQL.")
