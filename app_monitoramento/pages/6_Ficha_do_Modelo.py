"""Página 6 — Ficha do modelo: o que está em produção e quando retreinar."""

import streamlit as st

from config.theme import COR, DESTAQUE, como_ler, explicar, kpi, secao_titulo, virg
from utils import graficos
from utils.dados import carregar_clientes, carregar_ganho
from utils.pagina import abrir_pagina

dados, _ = abrir_pagina("Ficha do modelo", "O que está em produção e quando retreinar", imagem="ilustracao_modelo.png",
                        com_lote=False)
info = dados["gold_churn_modelo_info"].iloc[0]
fonte = dados["gold_churn_modelo_info__fonte"]

secao_titulo("O MODELO", f"{str(info['modelo']).replace('_', ' ')} sobre {int(info['n_variaveis'])} variáveis",
             "Escolhido entre seis modelos pela consistência entre treino, teste e base total (notebook 06).")
c1, c2, c3, c4 = st.columns(4, gap="medium")
with c1:
    kpi("ROC-AUC no teste", virg(float(info["roc_auc_teste"]), 3), "ordena bem quem sai na frente de quem fica")
with c2:
    kpi("Recall no teste", f"{virg(100 * float(info['recall_teste']), 0)}%", "de quem sai, quantos o modelo marca")
with c3:
    kpi("Precisão no teste", f"{virg(100 * float(info['precision_teste']), 0)}%", "dos marcados, quantos saem de fato")
with c4:
    kpi("Limiar do Yes", virg(float(info["limiar"]), 4), "maior F1 fora da dobra do treino")
st.code(str(info["parametros"]), language="text")
explicar("""- **ROC-AUC:** a chance de o modelo dar nota maior a um cliente que saiu do que a um que ficou (0,5 é sorteio; 1 é perfeito).
- **Recall:** de cada 100 clientes que saem, quantos o modelo marca como Yes.
- **Precisão:** de cada 100 marcados como Yes, quantos saem de fato.
- **Limiar:** a nota a partir da qual o cliente vira Yes; escolhido pelo maior F1 fora da dobra do treino.

Todos medidos no **teste**: clientes que o modelo não viu.""", "O que significam estas métricas")

secao_titulo("QUANTO O MODELO RENDE", "A curva de ganho",
             "Ordenando a carteira pela nota e contatando do maior para o menor risco: quanto de quem sai cada fatia alcança.")
try:
    ganho = carregar_ganho()
    pct_limiar = float(carregar_clientes()["Churn_Previsto"].mean())
    st.plotly_chart(graficos.curva_ganho(ganho, pct_limiar, "ganho_teste.csv (notebook 10, 5.2), clientes do teste"),
                    use_container_width=True, theme=None)
    como_ler("a distância entre a linha azul e a diagonal pontilhada (o sorteio).",
             "como a curva sobe rápido no começo: os primeiros decis concentram quem sai.",
             "o ponto laranja (20% da carteira) com o ponto preto (o limiar do modelo, cerca de 40%).",
             f"ligando para 20% da carteira, alcançamos {virg(100 * ganho.loc[1, 'captura_acum'], 0)}% de quem vai sair; "
             f"o grupo de maior risco tem {virg(100 * ganho.loc[0, 'taxa_churn'], 0)}% de churn real.",
    itens_legenda=[(COR, "o modelo", "linha"), ("#9CA3AF", "o sorteio (sem modelo)", "tracejado"), (DESTAQUE, "20% da carteira", "ponto"), ("#1A1A1A", "limiar do modelo", "ponto")],
    termos={"Curva de ganho": "ordena os clientes do teste pela nota, do maior para o menor risco, e mostra quanto de quem saiu cada fatia alcança.", "Lift": "quantas vezes melhor que o sorteio: nos 20% do topo, 48% ÷ 20% = 2,4 vezes."},
)
except FileNotFoundError as erro:
    st.info(f"Curva de ganho indisponível: {erro}")

secao_titulo("COMO O MONITOR DECIDE", "Os limites do semáforo")
st.markdown("""
| Indicador | Referência | Atenção | Alerta |
|---|---|---|---|
| PSI de cada variável | Treino (4.507 clientes) | 0,10 a 0,25 | Acima de 0,25 |
| PSI das notas | Teste (1.127 clientes, que o modelo não viu) | 0,10 a 0,25 | Acima de 0,25 |
| Taxa de Yes | Teste (cerca de 40%) | 5 a 10 pontos percentuais | Mais de 10 pontos |
| Reprodução pelo MLflow | Notas publicadas | Modelo não carregado | Notas diferentes |
| Recall e precisão reais | Teste (78% e 52%) | Queda de 5 a 10 pontos | Queda de mais de 10 pontos |
""")

secao_titulo("QUANDO RETREINAR", "As regras")
st.markdown("""
- **Alguma variável do núcleo em alerta** (contrato, tempo de casa, internet, pagamento): retreinar com o histórico atualizado (notebooks 04, 05 e 06).
- **Taxa de Yes a mais de 10 pontos do teste:** investigar a carteira; se a deriva se confirmar, retreinar.
- **Recall real mais de 10 pontos abaixo de 78%:** retreinar e rever o limiar.
- **MLflow em alerta:** não usar as notas; publicar de novo pelo notebook 06.
- **Indicadores em atenção:** acompanhar no lote seguinte e registrar o motivo provável.
""")
st.caption(f"Fonte: {fonte}. Monitoramento: notebook 09 · registro do modelo no MLflow: notebook 06, seção 6.")
