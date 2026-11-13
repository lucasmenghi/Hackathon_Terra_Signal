"""Página 5 — Fila de retenção: quem procurar primeiro."""

import streamlit as st

from config.theme import CINZA_CLARO, COR, DESTAQUE, como_ler, explicar, kpi, secao_titulo, virg
from utils import graficos
from utils.pagina import abrir_pagina

dados, _ = abrir_pagina("Fila de retenção", "Quem procurar primeiro, e com que oferta", imagem="ilustracao_fila.png",
                        com_lote=False)
fila = dados["gold_churn_fila_retencao"].copy()
fonte = dados["gold_churn_fila_retencao__fonte"]
perfil = dados["gold_churn_segmentos_perfil"]
nomes = dict(zip(perfil["segmento"], perfil["nome"]))
lote = fila["lote"].iloc[0] if "lote" in fila else "lote atual"

# ── Filtros ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("**Filtros da fila**")
    segs = st.multiselect("Segmento", sorted(fila["segmento"].dropna().unique()), format_func=lambda s: f"{s} {nomes.get(s, '')}")
    quads = st.multiselect("Quadrante", ["Salvar já", "Ação barata", "Fidelizar", "Manter"], default=["Salvar já", "Ação barata"])
    so_yes = st.checkbox("Só previstos como Yes", value=True)
f = fila
if segs:
    f = f[f["segmento"].isin(segs)]
if quads:
    f = f[f["quadrante"].isin(quads)]
if so_yes:
    f = f[f["Churn_Previsto"] == 1]

# ── Resumo ──────────────────────────────────────────────────────────────────────
n_yes = int(fila["Churn_Previsto"].sum())
salvar = fila[fila["quadrante"] == "Salvar já"]
receita = float(fila.loc[fila["Churn_Previsto"] == 1, "MonthlyCharges"].sum())
secao_titulo(f"LOTE {str(lote).upper()}", f"{virg(n_yes, 0)} de {virg(len(fila), 0)} clientes têm sinal de saída",
             "Risco alto = previsto como Yes pelo modelo; valor alto = mensalidade a partir da mediana do treino.")
c1, c2, c3 = st.columns(3, gap="medium")
with c1:
    kpi("Salvar já", virg(len(salvar), 0), "risco alto e mensalidade alta", cor_valor=DESTAQUE)
with c2:
    kpi("Receita com sinal de saída", f"R$ {virg(receita / 1000, 1)} mil/mês",
        "não é perda esperada: cerca de metade dos marcados sai (precisão de 52%)")
with c3:
    kpi("Na fila filtrada", virg(len(f), 0), "clientes com os filtros da barra lateral")

# ── Matriz risco × valor ────────────────────────────────────────────────────────
st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)
secao_titulo("QUEM PRIMEIRO", "A matriz risco × valor",
             "Risco alto = nota acima do limiar; valor alto = mensalidade a partir da mediana do treino (notebook 07).")
info_m = dados["gold_churn_modelo_info"].iloc[0]
valor_alto = float(fila.loc[fila["quadrante"].isin(["Salvar já", "Fidelizar"]), "MonthlyCharges"].min())
st.plotly_chart(graficos.matriz_risco_valor(fila, float(info_m["limiar"]), valor_alto, fonte), use_container_width=True, theme=None)
como_ler(
    "o canto de cima à direita (salvar já): risco alto e mensalidade alta.",
    "como os pontos se agrupam em faixas de mensalidade: são os pacotes (só telefone, DSL, fibra).",
    "salvar já (oferta forte) com ação barata (risco alto, mensalidade baixa: e-mail ou aviso no app).",
    "a fila começa pelo canto laranja; fidelizar e manter não pedem ação de retenção.",
    itens_legenda=[(DESTAQUE, "salvar já: risco alto, mensalidade alta", "ponto"), ("#E8B27A", "ação barata: risco alto, mensalidade baixa", "ponto"), (COR, "fidelizar: risco baixo, mensalidade alta", "ponto"), ("#C9CED3", "manter: risco baixo, mensalidade baixa", "ponto"), ("#4B5563", "limiar e mediana", "tracejado")],
    termos={"Nota de risco": "a probabilidade do modelo, usada para ordenar; não é a chance exata de sair.", "Faixas de mensalidade": "os grupos horizontais de pontos são os pacotes: só telefonia (cerca de R$ 20), DSL e fibra (acima de R$ 70)."},
)

# ── Segmento × quadrante ────────────────────────────────────────────────────────
st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)
secao_titulo("ONDE AGIR", "Em que segmento estão os clientes para salvar?",
             "Segmentos do notebook 07 (K-means no comportamento, sem o churn).")
st.plotly_chart(graficos.fila_por_segmento(fila, nomes, fonte), use_container_width=True, theme=None)
como_ler(
    "o laranja escuro (salvar já) de cada barra.",
    "em que segmento ele se concentra, e quanto do segmento ele ocupa.",
    "o laranja claro (ação barata: risco alto, mensalidade baixa) com o escuro.",
    "a campanha começa por um segmento só: fibra no contrato mensal com pouca proteção.",
    itens_legenda=[(DESTAQUE, "salvar já", "barra"), ("#F2C08F", "ação barata", "barra"), (COR, "fidelizar", "barra"), (CINZA_CLARO, "manter", "barra")],
)

# ── A fila ──────────────────────────────────────────────────────────────────────
secao_titulo("A FILA", "Clientes ordenados pela nota de risco",
             "A nota ordena a fila; ela não é a chance exata de sair (o balanceamento das classes infla a probabilidade).")
mostrar = f.rename(columns={"customerID": "Cliente", "Probabilidade_Churn": "Nota de risco", "Decil_Risco": "Decil",
                            "segmento": "Segmento", "quadrante": "Quadrante", "MonthlyCharges": "Mensalidade (R$)",
                            "Contract": "Contrato", "tenure": "Meses", "InternetService": "Internet",
                            "PaymentMethod": "Pagamento", "acao_sugerida": "Oferta sugerida"})
colunas = ["Cliente", "Nota de risco", "Decil", "Segmento", "Quadrante", "Mensalidade (R$)", "Contrato", "Meses",
           "Internet", "Pagamento", "Oferta sugerida"]
st.dataframe(mostrar[colunas], hide_index=True, use_container_width=True, height=420,
             column_config={"Nota de risco": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=1),
                            "Mensalidade (R$)": st.column_config.NumberColumn(format="%.2f")})
explicar("""- **Nota de risco:** a probabilidade do modelo; a barra mostra a nota de 0 a 1. Ordena a fila; não é a chance exata.
- **Decil:** D1 são os 10% de maior risco da carteira; D10, os de menor.
- **Segmento:** o tipo de cliente (notebook 07). S1 fibra no mensal com pouca proteção; S2 DSL no mensal, novos; S3 contrato anual; S4 só telefonia; S5 fiéis de dois anos.
- **Quadrante:** salvar já, ação barata, fidelizar ou manter, pelo risco e pela mensalidade.
- **Oferta sugerida:** a ação do segmento. A escada completa de cada cliente está na página Atendimento.""", "O que é cada coluna")
st.download_button("Baixar a fila filtrada (CSV)", mostrar[colunas].to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                   file_name=f"fila_retencao_{lote}.csv", mime="text/csv")
st.caption(f"Fonte: {fonte}.")
