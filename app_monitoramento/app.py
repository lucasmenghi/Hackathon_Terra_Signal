"""
app.py — Home da Central de retenção (atendimento e monitoramento do modelo de churn) (Terra Signal · Grupo 4).
Rodar localmente:   streamlit run app.py
No Databricks:      publicar a pasta como Databricks App (ver README.md).
"""

import streamlit as st

from config.theme import COR, DESTAQUE, TEXTO_2, aplicar_tema, card, imagem_base64, page_header, virg
from utils.dados import carregar_clientes, carregar_relatos
from utils.pagina import sidebar_header

st.set_page_config(page_title="Central de retenção · Terra Signal", layout="wide", initial_sidebar_state="expanded")
aplicar_tema()
sidebar_header()
page_header("Central de retenção", "Terra Signal · Hackathon Databricks · Grupo 4")


def porta(rotulo: str, titulo: str, texto: str, numeros: str, cor: str, modo: str, botao: str):
    st.markdown(f"""
<div style="background:#fff;border:1px solid #E5E7EB;border-top:5px solid {cor};border-radius:12px;padding:1.1rem 1.3rem;min-height:210px;">
  <p style="font-size:12.5px;font-weight:700;color:{cor};text-transform:uppercase;letter-spacing:0.08em;margin:0;">{rotulo}</p>
  <p style="font-size:1.45rem;font-weight:700;color:#1A1A1A;margin:4px 0 6px;">{titulo}</p>
  <p style="font-size:14.5px;color:#1A1A1A;line-height:1.55;margin:0 0 10px;">{texto}</p>
  <p style="font-size:14px;color:#1A1A1A;margin:0;">{numeros}</p>
</div>""", unsafe_allow_html=True)
    if st.button(botao, key=f"porta_{modo}", type="primary", use_container_width=True):
        st.session_state["modo"] = modo
        st.switch_page("pages/1_Atendimento.py")


try:
    _cl = carregar_clientes().merge(carregar_relatos(), on="customerID", how="left")
    _n = _cl["abordagem"].value_counts()
    _ret, _rec, _total = int(_n.get("Retenção", 0)), int(_n.get("Recuperação", 0)), len(_cl)
except Exception:
    _ret = _rec = _total = 0

st.markdown(f"""<p style="font-size:13px;font-weight:600;color:{TEXTO_2};text-transform:uppercase;letter-spacing:0.08em;margin:0 0 4px;">
    CADA CONVERSA É UMA CHANCE DE MANTER O CLIENTE</p>
<h2 style="font-size:1.7rem;font-weight:700;color:#1A1A1A;margin:0 0 1rem;">Como você vai atender hoje?</h2>""",
            unsafe_allow_html=True)
d1, d2 = st.columns(2, gap="large")
with d1:
    porta("O cliente chega até você", "Atendimento receptivo",
          "Busque o cliente pelo código e veja na hora o risco, o porquê, o que ele contou e a escada de ofertas.",
          f"<b>{virg(_total, 0)}</b> clientes da carteira pontuados pelo modelo", COR, "Receptivo", "Iniciar receptivo →")
with d2:
    porta("Você inicia a conversa", "Atendimento ativo",
          "A sua lista de ligações, separada pela conversa a ter e ordenada pela receptividade e pelo risco.",
          f"<b>{virg(_ret, 0)}</b> para retenção · <b>{virg(_rec, 0)}</b> para recuperação", DESTAQUE, "Ativo",
          "Abrir minha lista →")
st.markdown("<div style='height:1.6rem;'></div>", unsafe_allow_html=True)

col_esq, col_dir = st.columns([1, 1.2], gap="large")

with col_esq:
    st.markdown("""
<div style="margin-bottom: 1.2rem;">
    <p style="font-size:15px;color:#1A1A1A;line-height:1.7;margin:0;">
        O modelo de churn sai do notebook e vai para a ligação. Quando um cliente liga, a operadora vê na hora
        <b>o risco dele, o porquê e o que oferecer</b>, e simula a oferta antes de fazer. Para quem ainda não é
        cliente, o app compara pacotes e mostra qual fecha com menos risco de cancelamento.
    </p>
    <p style="font-size:13px;color:#4B5563;text-transform:uppercase;letter-spacing:0.05em;font-weight:600;margin:1rem 0 0;">
        Regressão logística Lasso · 41 variáveis · ROC-AUC 0,830 no teste
    </p>
    <p style="font-size:14px;color:#1A1A1A;margin:1rem 0 0;">
        Comece pelo <b>atendimento receptivo ou ativo</b>, acima. O <b>Plano de marketing</b> define as ofertas, a <b>Campanha</b> diz quantos clientes contatar, e as outras páginas mostram a fila do dia e se o modelo continua confiável.
    </p>
</div>
""", unsafe_allow_html=True)
    ilustracao = imagem_base64("ilustracao_home.png")
    if ilustracao:
        st.markdown(f'<img src="{ilustracao}" style="width:100%;max-width:520px;height:auto;margin-top:-1rem;" />',
                    unsafe_allow_html=True)

with col_dir:
    st.markdown("""
<p style="font-size:13px;font-weight:600;color:#4B5563;text-transform:uppercase;letter-spacing:0.08em;margin:0 0 6px;">
    PÁGINAS DO PAINEL</p>
<h2 style="font-size:1.7rem;font-weight:700;color:#1A1A1A;margin:0 0 1.1rem;">O que você quer ver hoje?</h2>
""", unsafe_allow_html=True)
    card("Plano de marketing", "As ofertas que a operadora pode fazer",
         "O marketing liga e desliga ofertas, escreve a fala, define a validade e os segmentos. A escada do atendimento "
         "segue o plano na hora.",
         ["Catálogo", "Falas", "Segmentos", "Impacto"])
    st.page_link("pages/8_Plano_de_marketing.py", label="Abrir o plano de marketing →")
    st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        card("Campanha de retenção", "Quantos clientes contatar",
             "Com o custo do contato, o aceite e o desconto, o tamanho de campanha com o maior lucro, decil a decil.",
             ["Lucro", "Campanha ótima", "Suposições"])
        st.page_link("pages/2_Campanha.py", label="Abrir a campanha →")
    with c2:
        card("Fila de retenção", "Quem procurar primeiro",
             "A matriz risco × valor e os clientes do lote ordenados pela nota, com segmento e oferta sugerida.",
             ["Risco × valor", "Salvar já", "Exportar"])
        st.page_link("pages/5_Fila_de_Retencao.py", label="Abrir a fila de retenção →")
    st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)
    c3, c4 = st.columns(2, gap="medium")
    with c3:
        card("Saúde do modelo", "O semáforo e as ações de cada lote",
             "Cada carteira que entra é comparada com o treino; cada indicador aceso vira uma ação: acompanhar, investigar ou retreinar.",
             ["Semáforo", "Ações", "Retreino"])
        st.page_link("pages/3_Saude_do_Modelo.py", label="Abrir a saúde do modelo →")
    with c4:
        card("Deriva das variáveis", "O que mudou na carteira",
             "PSI de cada variável sobre as zonas do semáforo e a mudança faixa a faixa, com o lote simulado para comparar.",
             ["PSI", "Faixa a faixa", "Simulação"])
        st.page_link("pages/4_Deriva_das_Variaveis.py", label="Abrir a deriva das variáveis →")
    st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)
    card("Ficha do modelo", "O que está em produção e quanto rende",
         "Modelo, limiar e métricas no teste, a curva de ganho, os limites do monitor e as regras de quando retreinar.",
         ["Lasso", "Curva de ganho", "Retreino"])
    st.page_link("pages/6_Ficha_do_Modelo.py", label="Abrir a ficha do modelo →")
    st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)
    card("Pergunte aos dados", "O Genie dentro do app",
         "Perguntas em português sobre a carteira, os segmentos, as ofertas e o monitoramento, com a tabela e o SQL da resposta.",
         ["Genie", "Português", "SQL"])
    st.page_link("pages/7_Pergunte_aos_dados.py", label="Abrir o Genie →")
