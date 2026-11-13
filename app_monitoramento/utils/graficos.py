"""
utils/graficos.py
Gráficos do app, nos princípios do Better Data Visualizations (Jonathan Schwabish):
- o título diz a conclusão, e não o tema; o subtítulo diz a medida e a unidade;
- uma cor de destaque para o que pede atenção, cinza para o contexto;
- rótulos direto nos dados, em vez de legenda; sem grade pesada, sem 3D, eixo de barras começando em zero;
- linhas de referência nomeadas no próprio gráfico; fonte no rodapé.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from config.theme import CINZA, CINZA_CLARO, COR, DESTAQUE, STATUS_COR, TEXTO, TEXTO_2, virg

FONTE = "Helvetica Neue, Helvetica, Arial, sans-serif"
QUAD_COR = {"Salvar já": DESTAQUE, "Ação barata": "#F2C08F", "Fidelizar": COR, "Manter": CINZA_CLARO}
QUAD_TEXTO = {"Salvar já": "white", "Ação barata": TEXTO, "Fidelizar": "white", "Manter": TEXTO}


def _layout(fig, titulo: str, subtitulo: str, fonte: str, altura: int = 420, margem_esq: int = 10):
    fig.update_layout(
        title=dict(text=f"<b>{titulo}</b><br><span style='font-size:13px;color:{TEXTO_2}'>{subtitulo}</span>",
                   x=0, xanchor="left", y=0.97, yanchor="top", font=dict(size=17, color="#1A1A1A")),
        font=dict(family=FONTE, size=13, color="#1A1A1A"),
        plot_bgcolor="white", paper_bgcolor="white", height=altura, showlegend=False, separators=",.",
        margin=dict(l=margem_esq, r=30, t=95, b=85),
    )
    fig.add_annotation(text=f"Fonte: {fonte}", xref="paper", yref="paper", x=0, y=0, yshift=-58, xanchor="left",
                       yanchor="top", showarrow=False, font=dict(size=13, color="#1A1A1A"))
    fig.update_xaxes(showgrid=False, zeroline=False, showline=True, linecolor="#9CA3AF", ticks="",
                     tickfont=dict(color="#1A1A1A", size=13), title_font=dict(color="#1A1A1A", size=13), automargin=True)
    fig.update_yaxes(showgrid=False, zeroline=False, ticks="", tickfont=dict(color="#1A1A1A", size=13), automargin=True,
                     title_font=dict(color="#1A1A1A", size=13))
    return fig


def psi_por_variavel(ind: pd.DataFrame, fonte: str):
    """Barras horizontais do PSI de cada indicador, sobre as zonas do semáforo."""
    d = ind[ind["unidade"] == "PSI"].sort_values("valor")
    lim_at, lim_al = float(d["limite_atencao"].iloc[0]), float(d["limite_alerta"].iloc[0])
    n_fora = int((d["valor"] >= lim_at).sum())
    titulo = ("Nada mudou em relação ao treino: todos os PSI na zona estável" if n_fora == 0 else
              f"{n_fora} {'indicador saiu' if n_fora == 1 else 'indicadores saíram'} da zona estável")
    cores = [STATUS_COR["alerta"] if v >= lim_al else DESTAQUE if v >= lim_at else COR for v in d["valor"]]
    xmax = max(d["valor"].max() * 1.2, lim_al * 1.25)
    fig = go.Figure()
    faixas_semaforo(fig, lim_at, lim_al, xmax)
    fig.add_trace(go.Bar(x=d["valor"], y=d["indicador"], orientation="h", marker_color=cores, width=0.55,
                         text=[virg(v, 3) for v in d["valor"]], textposition="outside", cliponaxis=False,
                         textfont=dict(size=13, color="#1A1A1A"), hovertemplate="%{y}: PSI %{x:.3f}<extra></extra>"))
    fig.update_xaxes(range=[0, xmax], title_text="PSI: quanto a carteira se afastou do treino (0 = igual)", tickformat=".2f")
    return _layout(fig, titulo, "PSI de cada variável, lote contra o treino, sobre as zonas do semáforo (0,10 e 0,25)", fonte,
                   altura=150 + 36 * len(d))


def faixas_semaforo(fig, lim_at: float, lim_al: float, xmax: float):
    """Fundo do gráfico pintado com as zonas do semáforo, com o nome de cada zona no topo."""
    for x0, x1, cor, nome in [(0, lim_at, "#EEF6F0", "estável"), (lim_at, lim_al, "#FDF6E3", "atenção"),
                              (lim_al, xmax, "#FBECEA", "alerta")]:
        fig.add_vrect(x0=x0, x1=x1, fillcolor=cor, line_width=0, layer="below")
        fig.add_annotation(x=(x0 + x1) / 2, y=1.0, yref="paper", yanchor="bottom", text=f"<b>{nome}</b>", showarrow=False,
                           font=dict(size=12.5, color=STATUS_COR[nome]))


def halteres(ind_a: pd.DataFrame, ind_b: pd.DataFrame, nome_a: str, nome_b: str, fonte: str):
    """PSI de dois lotes lado a lado (gráfico de halteres), sobre as zonas do semáforo."""
    a = ind_a[ind_a["unidade"] == "PSI"].set_index("indicador")["valor"]
    b = ind_b[ind_b["unidade"] == "PSI"].set_index("indicador")["valor"]
    d = pd.DataFrame({"a": a, "b": b}).dropna().sort_values("b")
    lims = ind_b.loc[ind_b["unidade"] == "PSI", ["limite_atencao", "limite_alerta"]].dropna()
    lim_at, lim_al = (float(lims.iloc[0, 0]), float(lims.iloc[0, 1])) if len(lims) else (0.10, 0.25)
    xmax = max(d.max().max() * 1.2, lim_al * 1.25)
    fig = go.Figure()
    faixas_semaforo(fig, lim_at, lim_al, xmax)
    for nome, linha in d.iterrows():
        fig.add_trace(go.Scatter(x=[linha["a"], linha["b"]], y=[nome, nome], mode="lines",
                                 line=dict(color="#C9CED3", width=3), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=d["a"], y=d.index, mode="markers", marker=dict(color="#8A9199", size=11),
                             hovertemplate=f"{nome_a} · %{{y}}: PSI %{{x:.3f}}<extra></extra>"))
    cores_b = [STATUS_COR["alerta"] if v >= lim_al else DESTAQUE if v >= lim_at else COR for v in d["b"]]
    fig.add_trace(go.Scatter(x=d["b"], y=d.index, mode="markers+text", marker=dict(color=cores_b, size=13),
                             text=[virg(v, 3) for v in d["b"]], textposition="middle right", textfont=dict(size=13, color="#1A1A1A"),
                             hovertemplate=f"{nome_b} · %{{y}}: PSI %{{x:.3f}}<extra></extra>"))
    base = d.index[0]
    fig.add_annotation(x=d.loc[base, "a"], y=base, text=f"● {nome_a}", xanchor="left", yshift=-22, showarrow=False,
                       font=dict(size=13, color="#1A1A1A"))
    fig.add_annotation(x=d.loc[d.index[-1], "b"], y=d.index[-1], text=f"● {nome_b}", xanchor="right", yshift=22,
                       showarrow=False, font=dict(size=12.5, color=DESTAQUE))
    n_at = int(((d["b"] >= lim_at) & (d["b"] < lim_al)).sum())
    n_al = int((d["b"] >= lim_al).sum())
    partes = ([f"{n_al} em alerta"] if n_al else []) + ([f"{n_at} em atenção"] if n_at else [])
    titulo = (f"No {nome_b.lower()}, {' e '.join(partes)}; na {nome_a.lower()}, tudo estável" if partes
              else "Os dois lotes ficam estáveis")
    fig.update_xaxes(range=[0, xmax], title_text="PSI: quanto a carteira se afastou do treino (0 = igual)", tickformat=".2f",
                     showgrid=False)
    
    return _layout(fig, titulo, "PSI de cada variável nos dois lotes, sobre as zonas do semáforo (0,10 e 0,25)",
                   fonte, altura=150 + 38 * len(d), margem_esq=10)


def distribuicao(dist: pd.DataFrame, variavel: str, nome_variavel: str, nome_lote: str, fonte: str):
    """Diferença lote − referência em cada faixa, em pontos percentuais: para a direita, a faixa cresceu."""
    d = dist[dist["variavel"] == variavel].sort_values("ordem", ascending=False)
    dif = (100 * (d["pct_lote"] - d["pct_referencia"])).to_numpy()
    faixas = d["faixa"].astype(str).to_numpy()
    if variavel == "segmento":                                   # S1 → "S1 · Fibra no mensal, pouca proteção"
        from config.theme import SEGMENTOS
        faixas = np.array([f"{f} · {SEGMENTOS[f][0]}" if f in SEGMENTOS else f for f in faixas])
    imax = int(abs(dif).argmax())
    titulo = (f"Em {nome_variavel.lower()}, a maior mudança é na faixa “{faixas[imax]}”: "
              f"{'+' if dif[imax] >= 0 else '−'}{virg(abs(dif[imax]), 1)} ponto{'s' if abs(dif[imax]) >= 2 else ''} percentua"
              f"{'is' if abs(dif[imax]) >= 2 else 'l'}")
    cores = [DESTAQUE if i == imax else (COR if v >= 0 else "#8A9199") for i, v in enumerate(dif)]
    textos = [f"{'+' if v >= 0 else '−'}{virg(abs(v), 1)}  ·  {virg(100 * l, 1)}% contra {virg(100 * r, 1)}%"
              for v, l, r in zip(dif, d["pct_lote"], d["pct_referencia"])]
    lim = max(abs(dif).max(), 1.0) * 2.4
    fig = go.Figure(go.Bar(x=dif, y=faixas, orientation="h", marker_color=cores, width=0.55, text=textos,
                           textposition="outside", cliponaxis=False, textfont=dict(size=13, color="#1A1A1A"),
                           hovertemplate="%{y}: %{x:+.1f} p.p.<extra></extra>"))
    fig.add_vline(x=0, line=dict(color="#4B5563", width=1))
    fig.add_annotation(x=lim * 0.98, y=1.02, yref="paper", xanchor="right", text="<b>mais clientes no lote →</b>",
                       showarrow=False, font=dict(size=13, color=COR))
    fig.add_annotation(x=-lim * 0.98, y=1.02, yref="paper", xanchor="left", text="<b>← menos clientes no lote</b>",
                       showarrow=False, font=dict(size=13, color="#4B5563"))
    fig.update_xaxes(range=[-lim, lim], title_text="diferença em pontos percentuais (lote − treino)", ticksuffix="")
    return _layout(fig, titulo, f"{nome_variavel}: diferença de cada faixa entre {nome_lote} e o treino · "
                   "texto = % no lote contra % no treino", fonte, altura=150 + 40 * len(d))


def taxa_yes(monit: pd.DataFrame, ordem_lotes: list, fonte: str):
    """Taxa de Yes por lote, contra a faixa de tolerância em torno da referência."""
    d = monit[monit["indicador"] == "Taxa de Yes"].drop_duplicates("lote", keep="last").set_index("lote").reindex(ordem_lotes).dropna(subset=["valor"])
    ref = float(d["referencia"].iloc[0])
    lim_at, lim_al = float(d["limite_atencao"].iloc[0]), float(d["limite_alerta"].iloc[0])
    from utils.dados import nome_lote
    nomes = [nome_lote(l) for l in d.index]
    cores = [STATUS_COR[s] if s != "estável" else COR for s in d["status"]]
    fig = go.Figure(go.Bar(x=nomes, y=d["valor"], marker_color=cores, text=[f"{virg(v, 1)}%" for v in d["valor"]],
                           textposition="outside", cliponaxis=False, width=0.45,
                           hovertemplate="%{x}: %{y:.1f}%<extra></extra>"))
    fig.add_hrect(y0=ref - lim_at, y1=ref + lim_at, fillcolor="#E8F3EA", line_width=0, layer="below")
    fig.add_hline(y=ref, line=dict(color="#4B5563", dash="dot", width=1))
    fig.add_annotation(x=1, xref="paper", y=ref, text=f"teste: {virg(ref, 1)}%", xanchor="left", showarrow=False,
                       font=dict(size=13, color="#1A1A1A"))
    fig.add_annotation(x=1, xref="paper", y=ref + lim_at, text=f"tolerância ±{virg(lim_at, 0)} p.p.", xanchor="left",
                       yanchor="bottom", showarrow=False, font=dict(size=13, color="#2F6B3A"))
    fora = [n.lower() if n.startswith("Lote") else n for n, s in zip(nomes, d["status"]) if s != "estável"]
    titulo = ("A taxa de Yes está dentro da tolerância em todos os lotes" if not fora else
              f"A taxa de Yes sai da tolerância no {', '.join(fora)}")
    fig.update_yaxes(range=[0, max(d["valor"].max(), ref + lim_al) * 1.2], ticksuffix="%", showgrid=True,
                     gridcolor="#F0F0F0")
    fig = _layout(fig, titulo, "% de clientes previstos como Yes, por lote · faixa verde = referência ± 5 p.p.", fonte,
                  altura=380)
    fig.update_layout(margin=dict(r=140))
    return fig


def fila_por_segmento(fila: pd.DataFrame, nomes: dict, fonte: str):
    """Clientes de cada segmento por quadrante de risco × valor, barras empilhadas com rótulos dentro."""
    ordem_q = ["Salvar já", "Ação barata", "Fidelizar", "Manter"]
    tab = pd.crosstab(fila["segmento"], fila["quadrante"]).reindex(columns=ordem_q, fill_value=0)
    tab = tab.loc[sorted(tab.index, reverse=True)]
    rotulos = [f"{s}  {nomes.get(s, '')}" for s in tab.index]
    fig = go.Figure()
    for q in ordem_q:
        v = tab[q]
        fig.add_trace(go.Bar(y=rotulos, x=v, orientation="h", name=q, marker_color=QUAD_COR[q],
                             text=[str(int(x)) if x >= 25 else "" for x in v], textposition="inside",
                             insidetextanchor="middle", textfont=dict(color=QUAD_TEXTO[q], size=13),
                             hovertemplate=f"{q} · %{{y}}: %{{x}} clientes<extra></extra>"))
    fig.update_layout(barmode="stack", bargap=0.35)
    # legenda escrita no topo, na ordem das barras (rótulo direto, sem caixa de legenda)
    pos = 0
    for q in ordem_q:
        fig.add_annotation(x=pos, xref="paper", y=1.06, yref="paper", xanchor="left", showarrow=False,
                           text=f"<span style='color:{QUAD_COR[q] if q != 'Manter' else '#9CA3AF'}'>■</span> {q}",
                           font=dict(size=11.5, color=TEXTO))
        pos += 0.17
    seg_top = tab["Salvar já"].idxmax()
    titulo = (f"{seg_top} concentra {int(tab.loc[seg_top, 'Salvar já'])} dos {int(tab['Salvar já'].sum())} clientes "
              "para “salvar já”")
    fig.update_xaxes(title_text="clientes")
    return _layout(fig, titulo, "Clientes do lote por segmento e quadrante de risco × valor", fonte,
                   altura=140 + 52 * len(tab), margem_esq=10)


# ── Atendimento ─────────────────────────────────────────────────────────────────

def motivos_cliente(mot: pd.DataFrame):
    """Barras do efeito de cada tema na nota do cliente: laranja empurra o risco para cima, cinza protege."""
    d = mot.iloc[::-1]
    cores = [DESTAQUE if v > 0 else CINZA for v in d["efeito"]]
    rotulos = [f"{t}  ·  {desc}" for t, desc in zip(d.index, d["descricao"])]
    fig = go.Figure(go.Bar(x=d["efeito"], y=rotulos, orientation="h", marker_color=cores,
                           hovertemplate="%{y}<br>efeito %{x:+.2f}<extra></extra>"))
    fig.add_vline(x=0, line=dict(color="#999999", width=1))
    lim = max(abs(d["efeito"]).max() * 1.15, 0.5)
    fig.update_xaxes(range=[-lim, lim], showticklabels=False, showline=False)
    fig.add_annotation(x=lim, y=1.03, yref="paper", xanchor="right", text="aumenta o risco →", showarrow=False,
                       font=dict(size=12.5, color=DESTAQUE))
    fig.add_annotation(x=-lim, y=1.03, yref="paper", xanchor="left", text="← protege", showarrow=False,
                       font=dict(size=13, color="#1A1A1A"))
    topo = mot.index[0]
    titulo = (f"O que mais pesa: {topo.lower()} ({mot['descricao'].iloc[0]})" if mot["efeito"].iloc[0] > 0
              else "Nenhum tema empurra o risco para cima")
    return _layout(fig, titulo, "Quanto cada tema soma na nota deste cliente, em relação a um cliente médio do treino",
                   "modelo oficial (notebook 06) · motor do notebook 10", altura=120 + 38 * len(d))


def escada(antes: float, opcoes: list, limiar: float):
    """Nota antes e depois de cada oferta (halteres): a distância é o quanto a oferta ajuda, segundo o modelo."""
    rot = [o[0] for o in opcoes][::-1]
    dep = [o[1] for o in opcoes][::-1]
    fig = go.Figure()
    for y, d in zip(rot, dep):
        fig.add_trace(go.Scatter(x=[antes, d], y=[y, y], mode="lines", line=dict(color=CINZA_CLARO, width=6), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[antes] * len(rot), y=rot, mode="markers", marker=dict(color=CINZA, size=13),
                             hovertemplate="hoje: %{x:.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=dep, y=rot, mode="markers+text", marker=dict(color=[COR if d < limiar else DESTAQUE for d in dep], size=15),
                             text=[virg(d, 2) for d in dep], textposition="bottom center", textfont=dict(size=13),
                             hovertemplate="depois da oferta: %{x:.2f}<extra></extra>"))
    fig.add_vline(x=limiar, line=dict(color="#BBBBBB", dash="dot", width=1))
    fig.add_annotation(x=limiar, y=1.03, yref="paper", text=f"limiar {virg(limiar, 2)}", showarrow=False,
                       font=dict(size=13, color="#1A1A1A"))
    fig.add_annotation(x=antes, y=1.03, yref="paper", text=f"hoje {virg(antes, 2)}", showarrow=False,
                       font=dict(size=13, color="#1A1A1A"))
    fig.update_xaxes(range=[0, 1], tickformat=".1f", title_text="nota de risco (0 a 1)")
    melhor = min(dep) if dep else antes
    titulo = (f"Com a oferta, a nota vai de {virg(antes, 2)} para {virg(melhor, 2)}"
              + (" e sai da zona de risco" if melhor < limiar <= antes else ""))
    return _layout(fig, titulo, "Cinza = nota hoje · azul = abaixo do limiar depois da oferta · laranja = continua acima",
                   "modelo oficial (notebook 06) · motor do notebook 10", altura=130 + 62 * len(rot), margem_esq=10)


def pacotes(opc: pd.DataFrame, limiar: float):
    """Nota de risco de cada variação do pacote: o pedido em cinza escuro, o recomendado em laranja."""
    d = opc.iloc[::-1]
    cores = [DESTAQUE if r else ("#4B5563" if p else CINZA_CLARO) for r, p in zip(d["recomendado"], d["pedido"])]
    fig = go.Figure(go.Bar(x=d["nota"], y=d["rotulo"], orientation="h", marker_color=cores,
                           text=[f"{virg(n, 2)}  ·  R$ {virg(m, 2)}" for n, m in zip(d["nota"], d["mensalidade"])],
                           textposition="outside", cliponaxis=False,
                           hovertemplate="%{y}<br>nota %{x:.2f}<extra></extra>"))
    fig.add_vline(x=limiar, line=dict(color="#BBBBBB", dash="dot", width=1))
    fig.add_annotation(x=limiar, y=1.02, yref="paper", text=f"limiar {virg(limiar, 2)}", showarrow=False,
                       font=dict(size=13, color="#1A1A1A"))
    fig.update_xaxes(range=[0, 1.25], showticklabels=False, showline=False)
    ped, rec = opc[opc["pedido"]].iloc[0], opc[opc["recomendado"]].iloc[0]
    titulo = f"O pacote recomendado baixa a nota de {virg(ped['nota'], 2)} para {virg(rec['nota'], 2)}"
    return _layout(fig, titulo, "Nota de risco no primeiro mês e mensalidade estimada · cinza escuro = pedido · laranja = recomendado",
                   "tabela de preço e modelo oficial · motor do notebook 10", altura=120 + 30 * len(d))


# ── Curva de ganho, campanha e matriz risco × valor ─────────────────────────────

def curva_ganho(ganho: pd.DataFrame, limiar_pct: float, fonte: str):
    """% de quem sai alcançado × % da carteira contatada, do maior para o menor risco, contra o sorteio."""
    x = [0] + list(100 * ganho["pct_carteira_acum"])
    y = [0] + list(100 * ganho["captura_acum"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, 100], y=[0, 100], mode="lines", line=dict(color="#9CA3AF", dash="dot", width=1.5),
                             hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", line=dict(color=COR, width=3), marker=dict(size=7, color=COR),
                             hovertemplate="contatando %{x:.0f}% da carteira: %{y:.0f}% de quem sai<extra></extra>"))
    y20 = float(100 * ganho.loc[1, "captura_acum"])
    fig.add_trace(go.Scatter(x=[20], y=[y20], mode="markers+text", marker=dict(size=14, color=DESTAQUE),
                             text=[f"<b>20% → {virg(y20, 0)}%</b>"], textposition="middle left", textfont=dict(size=14, color=DESTAQUE),
                             hoverinfo="skip"))
    y_lim = float(np.interp(100 * limiar_pct, x, y))
    fig.add_trace(go.Scatter(x=[100 * limiar_pct], y=[y_lim], mode="markers+text", marker=dict(size=11, color="#1A1A1A"),
                             text=[f"limiar do modelo: {virg(100 * limiar_pct, 0)}% → {virg(y_lim, 0)}%"],
                             textposition="bottom right", textfont=dict(size=13, color="#1A1A1A"), hoverinfo="skip"))
    fig.add_annotation(x=70, y=62, text="ao acaso: contatar 20% alcança 20%", showarrow=False, textangle=-33,
                       font=dict(size=13, color="#4B5563"))
    fig.update_xaxes(range=[0, 101], title_text="% da carteira contatada (do maior para o menor risco)", ticksuffix="%", dtick=10)
    fig.update_yaxes(range=[0, 103], title_text="% de quem sai alcançado", ticksuffix="%", dtick=20, showgrid=True,
                     gridcolor="#F0F0F0")
    return _layout(fig, f"Ligando para 20% da carteira, a retenção alcança {virg(y20, 0)}% de quem vai sair",
                   f"Curva de ganho no teste (clientes que o modelo não viu) · {virg(y20 / 20, 1)} vezes o sorteio nos 20% do topo",
                   fonte, altura=470)


def lucro_campanha(sim: pd.DataFrame, n_limiar: int, fonte: str):
    """Lucro esperado da campanha por % da carteira contatada, com o ótimo e o limiar do modelo marcados."""
    i = int(sim["lucro"].idxmax())
    ot, lim = sim.loc[i], sim.loc[min(n_limiar, len(sim) - 1)]
    fig = go.Figure()
    fig.add_hline(y=0, line=dict(color="#4B5563", width=1))
    fig.add_trace(go.Scatter(x=100 * sim["pct_carteira"], y=sim["lucro"], mode="lines", line=dict(color=COR, width=3),
                             hovertemplate="contatando %{x:.0f}%: lucro R$ %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[100 * ot["pct_carteira"]], y=[ot["lucro"]], mode="markers+text", marker=dict(size=15, color=DESTAQUE),
                             text=[f"<b>ótimo: {int(ot['n'])} clientes · R$ {virg(ot['lucro'] / 1000, 1)} mil</b>"],
                             textposition="top center", textfont=dict(size=14, color=DESTAQUE), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[100 * lim["pct_carteira"]], y=[lim["lucro"]], mode="markers+text", marker=dict(size=11, color="#1A1A1A"),
                             text=[f"limiar do modelo ({int(lim['n'])}): R$ {virg(lim['lucro'] / 1000, 1)} mil"],
                             textposition="bottom center", textfont=dict(size=13, color="#1A1A1A"), hoverinfo="skip"))
    topo = max(sim["lucro"].max(), 1)
    fig.update_xaxes(range=[0, 101], title_text="% da carteira contatada (do maior para o menor risco)", ticksuffix="%", dtick=10)
    fig.update_yaxes(range=[min(sim["lucro"].min() * 1.15, -0.08 * topo), topo * 1.25], title_text="lucro esperado (R$)",
                     tickformat=",.0f", showgrid=True, gridcolor="#F0F0F0")
    perto = abs(ot["lucro"] - lim["lucro"]) <= 0.05 * abs(ot["lucro"])
    if int(ot["n"]) == 0:
        titulo = "Com essas suposições, nenhuma campanha dá lucro: o custo supera o valor mantido em todos os grupos"
    else:
        titulo = (f"Contatar os {int(ot['n'])} clientes de maior risco ({virg(100 * ot['pct_carteira'], 0)}% da carteira) dá o maior lucro"
                  + (": o limiar do modelo fica perto do ótimo" if perto else ""))
    return _layout(fig, titulo, "Lucro esperado no horizonte escolhido = valor mantido − desconto para quem ficaria − custo dos contatos",
                   fonte, altura=460)


def matriz_risco_valor(fila: pd.DataFrame, limiar: float, valor_alto: float, fonte: str):
    """Um ponto por cliente: nota × mensalidade, com os quadrantes de ação; 'salvar já' em destaque."""
    cores = {"Salvar já": DESTAQUE, "Ação barata": "#E8B27A", "Fidelizar": COR, "Manter": "#C9CED3"}
    fig = go.Figure()
    for q in ["Manter", "Fidelizar", "Ação barata", "Salvar já"]:
        d = fila[fila["quadrante"] == q]
        fig.add_trace(go.Scatter(x=d["Probabilidade_Churn"], y=d["MonthlyCharges"], mode="markers",
                                 marker=dict(size=6 if q != "Salvar já" else 7, color=cores[q], opacity=0.75 if q != "Salvar já" else 0.9),
                                 customdata=d["customerID"], hovertemplate="%{customdata}<br>nota %{x:.2f} · R$ %{y:.2f}<extra></extra>"))
    fig.add_vline(x=limiar, line=dict(color="#4B5563", dash="dot", width=1))
    fig.add_hline(y=valor_alto, line=dict(color="#4B5563", dash="dot", width=1))
    ymax = float(fila["MonthlyCharges"].max()) * 1.08
    for q, x, y, anc in [("Salvar já", 0.99, ymax, "right"), ("Fidelizar", 0.01, ymax, "left"),
                         ("Ação barata", 0.99, 19, "right"), ("Manter", 0.01, 19, "left")]:
        n = int((fila["quadrante"] == q).sum())
        fig.add_annotation(x=x, y=y, xanchor=anc, yanchor="top" if y == ymax else "bottom", showarrow=False,
                           text=f"<b>{q}</b> · {n}", font=dict(size=14, color=cores[q] if q != "Manter" else "#4B5563"))
    fig.update_xaxes(range=[0, 1], title_text=f"nota de risco (tracejado = limiar {virg(limiar, 2)})", tickformat=".1f")
    fig.update_yaxes(range=[15, ymax], title_text=f"mensalidade, R$ (tracejado = mediana {virg(valor_alto, 2)})", showgrid=False)
    n_s = int((fila["quadrante"] == "Salvar já").sum())
    return _layout(fig, f"{n_s} clientes estão no quadrante salvar já: risco alto e mensalidade alta",
                   "Cada ponto é um cliente da carteira · a ação depende do quadrante", fonte, altura=500)
