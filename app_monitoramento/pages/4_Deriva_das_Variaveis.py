"""Página 4 — Deriva das variáveis: o que mudou na carteira."""

import streamlit as st

from config.theme import COR, DESTAQUE, STATUS_COR, como_ler, secao_titulo
from utils import graficos
from utils.dados import lotes, nome_lote
from utils.pagina import abrir_pagina

dados, lote = abrir_pagina("Deriva das variáveis", "O que mudou na carteira em relação ao treino",
                           imagem="ilustracao_deriva.png")
monit = dados["gold_churn_monitoramento"]
dist = dados["gold_churn_monitoramento_distribuicao"]
fonte = dados["gold_churn_monitoramento__fonte"]
ind = monit[monit["lote"] == lote].drop_duplicates("indicador", keep="last")

NOME_VAR = {"Contract": "Tipo de contrato", "tenure": "Tempo de casa (meses)", "InternetService": "Tipo de internet",
            "PaymentMethod": "Forma de pagamento", "MonthlyCharges": "Mensalidade (R$)", "TechSupport_bin": "Suporte técnico",
            "OnlineSecurity_bin": "Segurança online", "SeniorCitizen": "Idoso", "segmento": "Segmento (07)",
            "Probabilidade_Churn": "Nota do modelo"}

# ── PSI por variável ────────────────────────────────────────────────────────────
secao_titulo("PSI POR VARIÁVEL", "Quais variáveis mudaram?",
             "O PSI (índice de estabilidade da população) é zero quando a carteira tem as mesmas proporções do treino. "
             "Acima de 0,10, vale investigar; acima de 0,25, o modelo pode estar desatualizado.")
st.plotly_chart(graficos.psi_por_variavel(ind, fonte), use_container_width=True, theme=None)
como_ler(
    "o comprimento de cada barra em relação às linhas pontilhadas.",
    "barras coloridas: só as que passam de 0,10 ganham cor; as estáveis ficam em cinza.",
    "as variáveis do núcleo do modelo (contrato, tempo de casa, internet, pagamento) com as de contexto.",
    "na carteira real, todas ficam perto de zero; no lote simulado, contrato, internet, mensalidade e segmento passam do limite.",
    itens_legenda=[(COR, "estável", "barra"), (DESTAQUE, "atenção", "barra"), (STATUS_COR["alerta"], "alerta", "barra"), ("#EEF6F0", "zona estável (PSI até 0,10)", "zona"), ("#FDF6E3", "atenção (0,10 a 0,25)", "zona"), ("#FBECEA", "alerta (acima de 0,25)", "zona")],
    termos={"PSI": "índice de estabilidade da população: soma, faixa a faixa, de (% no lote − % na referência) × ln(% no lote ÷ % na referência). Zero é igual à referência; até 0,10 é estável."},
)

# ── Dois lotes lado a lado ──────────────────────────────────────────────────────
todos = lotes(monit)
outros = [l for l in todos if l != lote]
if outros:
    secao_titulo("COMPARAR LOTES", "O monitor acende quando a carteira muda?",
                 "Cada linha liga o PSI da variável em dois lotes. O lote simulado tem peso 3 para clientes de fibra "
                 "no contrato mensal: um alarme que funciona precisa acender nele.")
    comparar = st.selectbox("Comparar com", outros, format_func=nome_lote)
    a, b = (lote, comparar) if not str(lote).startswith("simulacao") else (comparar, lote)
    ind_a = monit[monit["lote"] == a].drop_duplicates("indicador", keep="last")
    ind_b = monit[monit["lote"] == b].drop_duplicates("indicador", keep="last")
    st.plotly_chart(graficos.halteres(ind_a, ind_b, nome_lote(a), nome_lote(b), fonte), use_container_width=True, theme=None)
    como_ler(
        "a distância entre o ponto cinza e o colorido de cada linha.",
        "os pontos laranja: passaram do limite de atenção (0,10).",
        "as variáveis que a simulação mexeu com as que ela não mexeu (idoso, suporte técnico).",
        "o monitor separa uma carteira estável de uma que mudou, e aponta exatamente o que mudou.",
    itens_legenda=[("#8A9199", "primeiro lote (carteira real)", "ponto"), (COR, "segundo lote: estável", "ponto"), (DESTAQUE, "atenção", "ponto"), (STATUS_COR["alerta"], "alerta", "ponto"), ("#EEF6F0", "zona estável (PSI até 0,10)", "zona"), ("#FDF6E3", "atenção (0,10 a 0,25)", "zona"), ("#FBECEA", "alerta (acima de 0,25)", "zona")],
    termos={"Lote simulado": "a mesma carteira sorteada de novo com peso 3 para fibra no contrato mensal: um teste de que o alarme acende.", "PSI": "índice de estabilidade da população: soma, faixa a faixa, de (% no lote − % na referência) × ln(% no lote ÷ % na referência). Zero é igual à referência; até 0,10 é estável."},
)

# ── Distribuição faixa a faixa ──────────────────────────────────────────────────
secao_titulo("FAIXA A FAIXA", "Onde está a mudança?",
             "Escolha uma variável para ver quanto cada faixa ganhou ou perdeu de clientes em relação ao treino.")
variaveis = [v for v in NOME_VAR if v in set(dist["variavel"])]
ordem_psi = (ind.set_index("indicador")["valor"].reindex([NOME_VAR[v] for v in variaveis]).fillna(0).to_numpy())
padrao = variaveis[int(ordem_psi.argmax())]
var = st.selectbox("Variável", variaveis, index=variaveis.index(padrao), format_func=lambda v: NOME_VAR[v])
d_lote = dist[dist["lote"] == lote]
st.plotly_chart(graficos.distribuicao(d_lote, var, NOME_VAR[var], nome_lote(lote), fonte), use_container_width=True, theme=None)
como_ler(
    "para que lado vai cada barra: para a direita, a faixa ganhou clientes; para a esquerda, perdeu.",
    "o tamanho da barra, em pontos percentuais; o texto mostra o % no lote contra o % no treino.",
    "faixas vizinhas: uma mudança real costuma deslocar várias faixas no mesmo sentido.",
    "a faixa com a maior diferença aparece no título; é por ela que a investigação começa.",
    itens_legenda=[(COR, "faixa ganhou clientes no lote", "barra"), ("#8A9199", "faixa perdeu clientes", "barra"), (DESTAQUE, "maior mudança", "barra"), ("#4B5563", "nenhuma mudança (zero)", "linha")],
    termos={"Ponto percentual (p.p.)": "a diferença entre duas porcentagens: de 12,1% para 13,3% são +1,2 p.p.", "Faixas": "nas variáveis contínuas, os décimos do treino (cada faixa tem 10% dos clientes do treino); nas categóricas, as próprias categorias."},
)
