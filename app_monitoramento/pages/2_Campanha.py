"""Página 2 — Campanha: quantos clientes contatar para ter o maior retorno.

Usa a taxa real de churn de cada decil no teste (não a nota do modelo) e as suposições de custo, aceite e desconto
informadas na tela. A conta está em motor/campanha.py.
"""

import pandas as pd
import streamlit as st

from config.theme import COR, DESTAQUE, STATUS_COR, TEXTO_2, como_ler, explicar, kpi, secao_titulo, virg
from motor.campanha import corte_em_taxa, simular
from utils import graficos
from utils.dados import carregar_clientes, carregar_ganho, carregar_motor
from utils.pagina import abrir_pagina

abrir_pagina("Campanha de retenção", "Quantos clientes contatar para ter o maior retorno", imagem="ilustracao_campanha.png",
             com_lote=False, carregar=False)
try:
    clientes = carregar_clientes()
    ganho = carregar_ganho()
    motor = carregar_motor()
except FileNotFoundError as erro:
    st.error(f"Sem os dados da campanha: {erro}")
    st.stop()

# ── Suposições ──────────────────────────────────────────────────────────────────
secao_titulo("SUPOSIÇÕES", "Quanto custa e quanto funciona a ação de retenção?",
             "A organização não informou esses números: os valores abaixo são exemplos. Mude e veja a campanha ótima mudar.")
c1, c2, c3, c4 = st.columns(4, gap="large")
with c1:
    custo = st.number_input("Custo por contato (R$)", min_value=0.0, max_value=500.0, value=15.0, step=5.0,
                            help="Ligação, tempo da operadora e brinde, por cliente contatado")
with c2:
    aceite = st.slider("Aceite da oferta (%)", 0, 100, 30, step=5,
                       help="De cada 100 clientes contatados, quantos aceitam a oferta") / 100
with c3:
    desconto = st.slider("Desconto da oferta (%)", 0, 50, 10, step=5,
                         help="Desconto na mensalidade de quem aceita, durante o horizonte") / 100
with c4:
    horizonte = st.slider("Horizonte (meses)", 3, 24, 12, step=3, help="Por quanto tempo contamos a mensalidade mantida")

explicar("""- **Custo por contato:** quanto custa falar com um cliente (ligação, tempo da operadora, brinde).
- **Aceite da oferta:** de cada 100 contatados, quantos aceitam.
- **Desconto:** quanto da mensalidade é dado a quem aceita, durante o horizonte.
- **Horizonte:** por quantos meses contamos a mensalidade mantida.

São exemplos: a organização não informou esses números. Mude e veja o tamanho ótimo da campanha mudar.""", "O que são estas suposições")

sim = simular(clientes, ganho, custo, aceite, desconto, horizonte)
i = int(sim["lucro"].idxmax())
ot = sim.loc[i]
n_limiar = int(clientes["Churn_Previsto"].sum())
lim = sim.loc[n_limiar]
todos = sim.iloc[-1]

# ── Resultado ───────────────────────────────────────────────────────────────────
st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)
k1, k2, k3, k4 = st.columns(4, gap="medium")
with k1:
    if int(ot["n"]) == 0:
        kpi("Campanha ótima", "Nenhuma", "com essas suposições, contatar dá prejuízo em todos os grupos", cor_valor=DESTAQUE)
    else:
        kpi("Campanha ótima", f"{virg(int(ot['n']), 0)} clientes",
            f"os de maior risco · {virg(100 * ot['pct_carteira'], 0)}% da carteira", cor_valor=DESTAQUE)
with k2:
    kpi("Lucro esperado", f"R$ {virg(ot['lucro'] / 1000, 1)} mil", f"em {horizonte} meses · valor mantido menos os custos",
        cor_valor=COR if ot["lucro"] > 0 else DESTAQUE)
with k3:
    kpi("Clientes mantidos", virg(ot["clientes_mantidos"], 0), f"de {virg(ot['churners_contatados'], 0)} que sairiam entre os contatados")
with k4:
    kpi("Pelo limiar do modelo", f"R$ {virg(lim['lucro'] / 1000, 1)} mil", f"contatando os {n_limiar} marcados como Yes")

st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)
st.plotly_chart(graficos.lucro_campanha(sim, n_limiar, "taxa real de churn por decil no teste (notebook 10) e suposições da tela"),
                use_container_width=True, theme=None)
como_ler(
    "o ponto laranja: o tamanho de campanha com o maior lucro.",
    "a curva sobe enquanto os contatados têm churn alto e cai quando o desconto passa a ir para quem ficaria de qualquer jeito.",
    "o ótimo com o ponto preto (os clientes que o modelo marca como Yes) e com o fim da curva (contatar todo mundo: "
    f"R$ {virg(todos['lucro'] / 1000, 1)} mil).",
    "mude o custo e o aceite: com contato caro ou aceite baixo, o ótimo encolhe para os primeiros decis.",
    itens_legenda=[(COR, "lucro esperado por tamanho de campanha", "linha"), (DESTAQUE, "campanha de maior lucro", "ponto"), ("#1A1A1A", "limiar do modelo (os marcados como Yes)", "ponto"), ("#4B5563", "lucro zero", "linha")],
    termos={"Valor mantido": "mensalidade de quem ia sair, aceitou a oferta e ficou, com o desconto, no horizonte escolhido.", "Custo do desconto": "o desconto dado também a quem ficaria de qualquer jeito: é o que faz a curva cair no fim.", "Taxa real de churn": "o churn observado em cada décimo do teste (clientes que o modelo não viu), e não a nota do modelo."},
)

# ── Conta por decil ─────────────────────────────────────────────────────────────
secao_titulo("A CONTA, DECIL A DECIL", "Em que grupo vale a pena ligar?",
             "Para cada décimo da carteira (D1 = maior risco), o resultado de contatar só aquele grupo.")
d = clientes.copy()
d["decil"] = d["Decil_Risco"].astype(str).str.lstrip("D").astype(int)
taxa = dict(zip(ganho["decil"], ganho["taxa_churn"]))
linhas = []
for dec, g in d.groupby("decil"):
    t = taxa[dec]
    m = g["MonthlyCharges"]
    valor = (t * aceite * m * (1 - desconto) * horizonte).sum()
    custo_d = ((1 - t) * aceite * m * desconto * horizonte).sum()
    custo_c = custo * len(g)
    linhas.append({"Decil": f"D{dec}", "Clientes": len(g), "Churn real no teste": f"{virg(100 * t, 0)}%",
                   "Mensalidade média": f"R$ {virg(m.mean(), 2)}", "Valor mantido": f"R$ {virg(valor, 0)}",
                   "Custo (contato + desconto)": f"R$ {virg(custo_c + custo_d, 0)}",
                   "Resultado": valor - custo_c - custo_d})
tab = pd.DataFrame(linhas)
vale = tab["Resultado"] > 0
tab["Vale ligar?"] = vale.map({True: "sim", False: "não"})
tab["Resultado"] = tab["Resultado"].map(lambda v: f"R$ {virg(v, 0)}")
st.dataframe(tab, hide_index=True, use_container_width=True)
explicar("""**Cada linha é um décimo da carteira**, do maior risco (D1) para o menor (D10), com cerca de 141 clientes.

- **Churn real no teste:** de cada 100 clientes desse grupo no teste, quantos saíram de fato.
- **Valor mantido:** o que se preserva de mensalidade contatando só esse grupo, com o aceite e o desconto da tela.
- **Custo:** contatos + desconto para quem aceitou e ficaria de qualquer jeito.
- **Resultado e Vale ligar?:** valor mantido menos custo. Os primeiros decis costumam valer; nos últimos, quase ninguém sairia, e o desconto vira prejuízo.""", "Como ler a tabela")

t_corte = corte_em_taxa(custo, aceite, desconto, horizonte, float(clientes["MonthlyCharges"].mean()))
st.markdown(f"""
<div style="background:#fff;border:1px solid #E5E7EB;border-left:5px solid {COR};border-radius:10px;padding:0.9rem 1.1rem;margin-top:0.6rem;">
  <p style="font-size:13px;font-weight:700;color:{COR};text-transform:uppercase;letter-spacing:0.06em;margin:0;">A regra por trás (notebook 00)</p>
  <p style="font-size:14px;margin:6px 0 0;line-height:1.6;color:#1A1A1A;">
    Vale contatar um cliente quando o churn real do grupo dele passa de
    <b>(custo + aceite × mensalidade × desconto × horizonte) ÷ (aceite × mensalidade × horizonte)</b>.
    Com as suposições da tela e a mensalidade média da carteira (R$ {virg(clientes['MonthlyCharges'].mean(), 2)}),
    o corte é <b>{virg(100 * t_corte, 0) if t_corte < 10 else "—"}% de churn real</b>. É a regra p* = custo ÷ (sucesso × valor) do notebook 00,
    com o custo do desconto para quem ficaria de qualquer jeito.</p>
</div>""", unsafe_allow_html=True)
st.caption("A taxa de churn de cada decil é a observada nos clientes do teste, que o modelo não viu. A nota do modelo não "
           "entra na conta, porque é inflada pelo balanceamento (no D1, nota média 0,89 para 76% de churn real). Aceite e "
           f"desconto iguais para todos é uma simplificação; o registro dos atendimentos permite medir os dois. Fonte: notebook 10 (5.2).")
