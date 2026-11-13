"""Página 3 — Saúde do modelo: o semáforo de cada lote e as ações necessárias."""

import pandas as pd
import streamlit as st

from config.theme import COR, STATUS_COR, STATUS_FUNDO, como_ler, explicar, kpi, pill, secao_titulo, virg
from utils.acoes import acoes_do_lote, veredito
from utils import graficos
from utils.dados import lotes, nome_lote
from utils.pagina import abrir_pagina

dados, lote = abrir_pagina("Saúde do modelo", "O semáforo de cada lote, contra o que o modelo viu no treino",
                           imagem="ilustracao_saude.png")
monit = dados["gold_churn_monitoramento"]
fonte = dados["gold_churn_monitoramento__fonte"]
ind = monit[monit["lote"] == lote].drop_duplicates("indicador", keep="last")

# ── Resumo do lote ──────────────────────────────────────────────────────────────
contagem = ind["status"].value_counts()
n_alerta, n_atencao = int(contagem.get("alerta", 0)), int(contagem.get("atenção", 0))
status_geral = "alerta" if n_alerta else "atenção" if n_atencao else "estável"
frase = {"estável": "Tudo estável: o modelo pode seguir pontuando esta carteira.",
         "atenção": f"{n_atencao} indicador(es) em atenção: acompanhar no próximo lote.",
         "alerta": f"{n_alerta} indicador(es) em alerta: investigar a deriva antes de usar as notas."}[status_geral]
secao_titulo(f"LOTE {nome_lote(lote).upper()} · EXECUTADO EM {ind['data_execucao'].max()}", frase,
             "Cada indicador compara o lote com a referência: o treino para as variáveis, o teste para as notas.")

taxa = ind.set_index("indicador").loc["Taxa de Yes"]
nota = ind.set_index("indicador").loc["PSI das notas"]
rep = ind.set_index("indicador").loc["Reprodução pelo MLflow"]
psi_var = ind[(ind["grupo"] == "Entrada do modelo")]
c1, c2, c3, c4 = st.columns(4, gap="medium")
with c1:
    kpi("Taxa de Yes", f"{virg(taxa['valor'], 1)}%", f"teste: {virg(taxa['referencia'], 1)}% · tolerância ±5 p.p.",
        status=taxa["status"])
with c2:
    kpi("PSI das notas", virg(nota["valor"], 3), "distribuição das notas contra o teste", status=nota["status"])
with c3:
    n_fora = int((psi_var["status"] != "estável").sum())
    kpi("Variáveis que mudaram", f"{n_fora} de {len(psi_var)}", "PSI de 0,10 ou mais contra o treino",
        status="estável" if n_fora == 0 else ("alerta" if (psi_var["status"] == "alerta").any() else "atenção"))
with c4:
    kpi("Modelo no MLflow", {"estável": "Reproduz", "alerta": "Diverge", "atenção": "Não lido"}.get(rep["status"], "—"),
        rep["leitura"], status=rep["status"])

# ── Ações necessárias ───────────────────────────────────────────────────────────
acoes = acoes_do_lote(ind)
st_v, titulo_v, frase_v = veredito(acoes)
st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)
secao_titulo("AÇÕES NECESSÁRIAS", "O que fazer com este lote",
             "Cada indicador aceso vira uma ação, com quem faz e em que notebook. A mais grave decide o veredito.")
st.markdown(f"""
<div style="background:{STATUS_FUNDO[st_v]};border-left:6px solid {STATUS_COR[st_v]};border-radius:10px;padding:0.9rem 1.2rem;margin-bottom:0.8rem;">
  <p style="font-size:1.25rem;font-weight:700;color:{STATUS_COR[st_v]};margin:0;">{titulo_v}</p>
  <p style="font-size:14px;color:#1A1A1A;margin:4px 0 0;">{frase_v}</p>
</div>""", unsafe_allow_html=True)
if len(acoes):
    COR_TIPO = {"Parar": "#C0392B", "Retreinar": "#C0392B", "Investigar": "#E0A100", "Acompanhar": "#1f6f8b", "Aguardar": "#9CA3AF"}
    linhas_a = "".join(
        f"<tr><td><span class='ts-pill' style='background:white;border:1px solid {COR_TIPO[a.tipo]};color:{COR_TIPO[a.tipo]};'>{a.tipo}</span></td>"
        f"<td><b>{a.indicador}</b><br>{pill(a.status)}</td><td>{a.o_que_fazer}</td>"
        f"<td style='color:#4B5563'>{a.quem}</td><td style='color:#4B5563'>{a.onde}</td></tr>" for a in acoes.itertuples())
    st.markdown(f"""
<table style="width:100%;border-collapse:collapse;font-size:13.5px;background:white;border:1px solid #E5E7EB;">
<thead><tr style="background:#4A4A4A;color:white;text-align:left;"><th style="padding:8px">Ação</th><th>Indicador</th>
<th>O que fazer</th><th>Quem</th><th>Onde</th></tr></thead><tbody>{linhas_a}</tbody></table>
""", unsafe_allow_html=True)

explicar("""**Cada linha é uma ação** que um indicador aceso pede, da mais grave para a mais leve:

- **Parar:** há um problema de dados ou de modelo; não usar as notas até corrigir.
- **Retreinar:** a carteira mudou no que o modelo mais usa (contrato, tempo de casa, internet, pagamento).
- **Investigar:** algo mudou; entender o quê antes de agir.
- **Acompanhar:** mudança pequena; olhar de novo no próximo lote.
- **Aguardar:** falta um dado (por exemplo, quem do lote saiu de fato).

**Quem** diz que time age; **Onde** aponta o notebook ou a página. A ação mais grave decide o veredito do lote.""", "Como ler as ações")

# ── Taxa de Yes por lote ────────────────────────────────────────────────────────
st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)
secao_titulo("SAÍDA DO MODELO", "O modelo está devolvendo o que devolvia?",
             "Se a carteira muda, a proporção de clientes marcados como Yes muda junto. A faixa verde é a tolerância.")
st.plotly_chart(graficos.taxa_yes(monit, lotes(monit), fonte), use_container_width=True, theme=None)
como_ler(
    "a altura de cada barra em relação à faixa verde.",
    "barras fora da faixa: o modelo está marcando bem mais (ou menos) clientes do que no teste.",
    "o lote real com o simulado, que tem mais clientes de fibra no contrato mensal.",
    "na carteira real, a taxa fica junto da do teste (cerca de 40%); no simulado, sobe para cerca de 60% e sai da faixa.",
    itens_legenda=[(COR, "lote dentro da tolerância", "barra"), (STATUS_COR["atenção"], "atenção (5 a 10 p.p.)", "barra"), (STATUS_COR["alerta"], "alerta (mais de 10 p.p.)", "barra"), ("#E8F3EA", "faixa de tolerância (±5 p.p.)", "zona"), ("#4B5563", "taxa de Yes no teste", "tracejado")],
    termos={"Taxa de Yes": "a parte dos clientes do lote que o modelo marca como risco de sair (nota acima do limiar 0,5046).", "Por que comparar com o teste": "o teste são clientes que o modelo não viu; se a carteira nova se parece com eles, a taxa fica parecida."},
)

# ── Tabela do semáforo ──────────────────────────────────────────────────────────
secao_titulo("TODOS OS INDICADORES", "O semáforo, indicador por indicador",
             "Recall e precisão reais ficam aguardando até a empresa saber quem do lote saiu de fato.")
ordem_grupo = ["Saída do modelo", "Entrada do modelo", "Qualidade dos dados", "Desempenho real"]
tab = ind.assign(o=ind["grupo"].map({g: i for i, g in enumerate(ordem_grupo)})).sort_values(["o", "indicador"])


def fmt(v, u):
    if pd.isna(v):
        return "—"
    return {"%": f"{virg(v, 1)}%", "PSI": virg(v, 3), "sim/não": "sim" if v >= 1 else "não"}.get(u, virg(v, 0))


linhas = "".join(
    f"<tr><td style='color:#4B5563'>{r.grupo}</td><td><b>{r.indicador}</b></td>"
    f"<td style='text-align:right'>{fmt(r.valor, r.unidade)}</td><td style='text-align:right;color:#4B5563'>{fmt(r.referencia, r.unidade)}</td>"
    f"<td>{pill(r.status)}</td><td style='color:#374151'>{r.leitura}</td></tr>"
    for r in tab.itertuples())
st.markdown(f"""
<table style="width:100%;border-collapse:collapse;font-size:13.5px;background:white;border:1px solid #E5E7EB;border-radius:8px;">
<thead><tr style="background:#4A4A4A;color:white;text-align:left;">
<th style="padding:8px">Grupo</th><th>Indicador</th><th style="text-align:right">Lote</th><th style="text-align:right">Referência</th>
<th>Semáforo</th><th>Leitura</th></tr></thead>
<tbody>{linhas}</tbody></table>
<style>tbody tr td {{ padding: 7px 8px; border-top: 1px solid #F0F0F0; }}</style>
""", unsafe_allow_html=True)
explicar("""- **Lote:** o valor do indicador na carteira escolhida na barra lateral.
- **Referência:** o que o modelo viu: o treino, para as variáveis; o teste, para as notas e a taxa de Yes.
- **Semáforo:** estável (verde), atenção (amarelo), alerta (vermelho), aguardando (cinza, falta o dado real).
- **PSI:** índice de estabilidade da população; 0 é igual à referência, até 0,10 é estável, acima de 0,25 é alerta.""", "Como ler o semáforo")
st.caption(f"Limites: PSI de 0,10 (atenção) e 0,25 (alerta); taxa de Yes a 5 e 10 pontos percentuais do teste. "
           f"Fonte: {fonte}.")
