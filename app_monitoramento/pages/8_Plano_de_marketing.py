"""Página 8 — Plano de marketing: o catálogo de ofertas que a operadora pode fazer.

O marketing liga e desliga ofertas, escreve a fala, define a validade e os segmentos. O Atendimento só mostra o que
está liberado aqui, e esta página mostra na hora quanto da fila o plano consegue tirar da zona de risco.
"""

import pandas as pd
import streamlit as st

from config.theme import COR, DESTAQUE, TEXTO_2, explicar, kpi, secao_titulo, virg
from utils import catalogo
from utils.dados import carregar_clientes, carregar_motor
from utils.pagina import abrir_pagina

abrir_pagina("Plano de marketing", "As ofertas que a operadora pode fazer, e quanto cada uma rende",
             imagem="ilustracao_campanha.png", com_lote=False, carregar=False)
try:
    motor = carregar_motor()
    clientes = carregar_clientes()
except FileNotFoundError as erro:
    st.error(f"Sem o motor de atendimento: {erro}")
    st.stop()


@st.cache_data(show_spinner="Calculando as ofertas da fila…")
def ofertas_da_fila() -> pd.DataFrame:
    fila = clientes[clientes["Churn_Previsto"] == 1].reset_index(drop=True)
    of = motor.ofertas_em_lote(fila)
    return of.merge(fila[["customerID", "segmento"]], on="customerID", how="left")


secao_titulo("CATÁLOGO DE OFERTAS", "O que a central pode oferecer hoje",
             "Ligue ou desligue cada oferta, ajuste a fala, a validade e os segmentos. O Atendimento muda na hora.")
cat = catalogo.catalogo().set_index("codigo")
editado = st.data_editor(
    cat, key="editor_catalogo", hide_index=True, use_container_width=True, num_rows="fixed",
    column_config={
        "Oferta": st.column_config.TextColumn("Oferta", disabled=True, width="medium"),
        "Ativa": st.column_config.CheckboxColumn("Ativa", help="Desligada, a oferta some da escada do atendimento"),
        "Fala para a operadora": st.column_config.TextColumn("Fala para a operadora", width="large",
                                                             help="O que a operadora diz ao oferecer"),
        "Válida até": st.column_config.DateColumn("Válida até", format="DD/MM/YYYY"),
        "Segmentos": st.column_config.TextColumn("Segmentos", help="Para quais segmentos vale, separados por vírgula (S1 a S5)"),
    })
catalogo.salvar(editado.reset_index().rename(columns={"index": "codigo"}))
c1, c2 = st.columns([1, 3])
with c1:
    if st.button("Voltar ao plano padrão"):
        st.session_state.pop("catalogo", None)
        st.session_state.pop("editor_catalogo", None)
        st.rerun()
explicar("""- **Ativa:** desligada, a oferta não aparece na escada de nenhum cliente (por exemplo, quando o estoque de desconto acaba).
- **Fala para a operadora:** o texto que aparece no cartão da oferta, no Atendimento.
- **Válida até:** depois dessa data, a oferta sai sozinha da escada.
- **Segmentos:** para quem a oferta vale (S1 fibra no contrato mensal, S2 DSL no contrato mensal, S3 contrato anual,
S4 só telefonia, S5 fiéis de dois anos).

Nesta versão, o plano fica na sessão do app e volta ao padrão quando a página é recarregada. Em produção, ele vira uma
tabela no Unity Catalog mantida pelo marketing, que o app lê ao abrir.""", "Como usar o catálogo")

# ── Impacto do plano na fila ────────────────────────────────────────────────────
of = ofertas_da_fila()
liberadas = {s: catalogo.liberadas(s) for s in of["segmento"].dropna().unique()}
ok = [all(a in liberadas.get(s, set()) for a in acoes) for acoes, s in zip(of["acoes"], of["segmento"])]
com_plano = of[ok]
n_fila = int((clientes["Churn_Previsto"] == 1).sum())


def melhores(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values("nota_depois").groupby("customerID").head(1)


todas_melhor, plano_melhor = melhores(of), melhores(com_plano)
saem_todas = int((todas_melhor["nota_depois"] < motor.limiar).sum())
saem_plano = int((plano_melhor["nota_depois"] < motor.limiar).sum())
sem_oferta = n_fila - plano_melhor["customerID"].nunique()

secao_titulo("IMPACTO NA FILA", f"Com este plano, {virg(saem_plano, 0)} dos {virg(n_fila, 0)} clientes da fila saem da zona de risco",
             "Pela nota do modelo, se cada cliente aceitar a melhor oferta liberada para ele.")
k1, k2, k3 = st.columns(3, gap="medium")
with k1:
    kpi("Saem da zona de risco", f"{virg(saem_plano, 0)} de {virg(n_fila, 0)}", "com a melhor oferta liberada no plano",
        cor_valor=COR)
with k2:
    kpi("Com todas as ofertas", f"{virg(saem_todas, 0)} de {virg(n_fila, 0)}", "o máximo que o catálogo completo alcança")
with k3:
    kpi("Sem oferta liberada", virg(sem_oferta, 0), "clientes da fila sem nenhuma oferta no plano",
        cor_valor=DESTAQUE if sem_oferta else TEXTO_2)

principais = (plano_melhor.groupby("oferta").agg(clientes=("customerID", "size"),
                                                 saem=("nota_depois", lambda v: int((v < motor.limiar).sum())),
                                                 queda=("reducao", "mean"))
              .sort_values("clientes", ascending=False).reset_index())
principais.columns = ["Oferta principal", "Clientes", "Saem da zona de risco", "Queda média da nota"]
principais["Queda média da nota"] = principais["Queda média da nota"].round(2)
st.dataframe(principais, hide_index=True, use_container_width=True)
explicar("""**Cada linha é uma oferta que vira a principal para algum cliente da fila** (os previstos como Yes), com quantos
clientes a recebem como primeira opção e quantos deles ficam abaixo do limiar se aceitarem.

Compare os cartões: a diferença entre **com este plano** e **com todas as ofertas** é o que o plano deixa na mesa.
Desligar o contrato de dois anos, por exemplo, mostra quanto da retenção depende dele.

É o efeito **pela nota do modelo**, não a retenção garantida: o aceite e a permanência reais se medem com um teste.""",
         "Como ler o impacto")
st.caption(f"Fila: clientes da carteira previstos como Yes (limiar {virg(motor.limiar, 2)}). Fonte: motor do notebook 10.")
