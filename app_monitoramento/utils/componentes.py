"""
utils/componentes.py
Barras desenhadas em HTML para a página Atendimento: ocupam a largura da coluna, não cortam rótulos e seguem os
cartões do app. Mesmos princípios dos gráficos (Schwabish): uma cor de destaque, cinza para o contexto, rótulos
direto nos dados, linha de referência nomeada.
"""

import streamlit as st

from config.theme import CINZA, CINZA_CLARO, COR, DESTAQUE, TEXTO_2, virg


def _forca(v: float) -> str:
    if v >= 1.0:
        return "pesa muito"
    if v >= 0.3:
        return "pesa"
    if v >= 0.05:
        return "pesa pouco"
    if v > -0.05:
        return "neutro"
    return "protege"


def motivos(mot) -> None:
    """Uma linha por tema: nome e dado do cliente à esquerda; barra a partir do zero (laranja = aumenta, cinza = protege)."""
    pos = max(float(mot["efeito"].clip(lower=0).max()), 1e-9)
    neg = max(float(-mot["efeito"].clip(upper=0).min()), 0.0)
    centro = 0.06 if neg < 1e-9 else min(max(neg / (neg + pos), 0.2), 0.5)      # onde fica o zero, em fração da trilha
    escala = max(pos, neg)
    linhas = []
    for tema, r in mot.iterrows():
        v = float(r["efeito"])
        larg = abs(v) / escala * (1 - centro if v >= 0 else centro) * 100
        esq = centro * 100 if v >= 0 else centro * 100 - larg
        cor = DESTAQUE if v >= 0.05 else (CINZA if v <= -0.05 else CINZA_CLARO)
        linhas.append(f"""
<div style="display:grid;grid-template-columns:42% 1fr 82px;align-items:center;gap:12px;padding:7px 0;border-top:1px solid #F0F0F0;">
  <div><b style="font-size:14px;">{tema}</b><br><span style="font-size:13px;color:{TEXTO_2};">{r['descricao']}</span></div>
  <div style="position:relative;height:16px;background:#F7F7F7;border-radius:3px;">
    <div style="position:absolute;left:{centro * 100:.1f}%;top:-3px;bottom:-3px;width:1px;background:#9CA3AF;"></div>
    <div style="position:absolute;left:{esq:.1f}%;width:{max(larg, 0.6):.1f}%;top:2px;bottom:2px;background:{cor};border-radius:2px;"></div>
  </div>
  <div style="font-size:13px;color:{DESTAQUE if v >= 0.05 else TEXTO_2};font-weight:600;">{_forca(v)}</div>
</div>""")
    st.markdown(f"""
<div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:0.6rem 1rem 0.4rem;">
  <div style="display:grid;grid-template-columns:42% 1fr 82px;gap:12px;font-size:13px;color:{TEXTO_2};padding-bottom:4px;">
    <span>TEMA · DADO DO CLIENTE</span><span>← protege &nbsp;|&nbsp; aumenta o risco →</span><span></span></div>
  {''.join(linhas)}
  <p style="font-size:13px;color:{TEXTO_2};margin:6px 0 0;">Em relação a um cliente médio do treino · modelo oficial (notebook 06)</p>
</div>""", unsafe_allow_html=True)


def regua(antes: float, depois: float | None, limiar: float, rotulo_depois: str = "com a oferta") -> None:
    """Régua de 0 a 1 com o limiar: ponto cinza = nota hoje; ponto colorido = nota depois da oferta."""
    def ponto(p, cor, texto, em_cima):
        pos = "bottom:22px;" if em_cima else "top:22px;"
        return (f'<div style="position:absolute;left:{p * 100:.1f}%;top:50%;width:16px;height:16px;margin:-8px 0 0 -8px;'
                f'border-radius:50%;background:{cor};border:2px solid #fff;box-shadow:0 0 0 1px {cor};"></div>'
                f'<div style="position:absolute;left:{p * 100:.1f}%;{pos}transform:translateX(-50%);white-space:nowrap;'
                f'font-size:13px;font-weight:600;color:{cor};">{texto}</div>')
    seta = ""
    marcas = ponto(antes, "#4B5563", f"hoje {virg(antes, 2)}", True)
    if depois is not None and abs(depois - antes) > 1e-6:
        a, b = sorted([antes, depois])
        seta = f'<div style="position:absolute;left:{a * 100:.1f}%;width:{(b - a) * 100:.1f}%;top:50%;height:4px;margin-top:-2px;background:#D1D5DB;"></div>'
        cor = COR if depois < limiar else DESTAQUE
        marcas += ponto(depois, cor, f"{rotulo_depois} {virg(depois, 2)}", False)
    st.markdown(f"""
<div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:2.2rem 1.6rem 2.4rem;margin:0.4rem 0 0.6rem;">
  <div style="position:relative;height:10px;background:linear-gradient(90deg,#EEF4F6 0%,#EEF4F6 {limiar * 100:.1f}%,#FBEFE3 {limiar * 100:.1f}%,#FBEFE3 100%);border-radius:5px;">
    {seta}
    <div style="position:absolute;left:{limiar * 100:.1f}%;top:-12px;bottom:-12px;border-left:1px dashed #9CA3AF;"></div>
    {marcas}
  </div>
  <div style="display:flex;justify-content:space-between;font-size:13px;color:{TEXTO_2};margin-top:30px;">
    <span>0 · menor risco</span><span>limiar {virg(limiar, 2)}: acima dele, o cliente entra na fila</span><span>1 · maior risco</span></div>
</div>""", unsafe_allow_html=True)


def pacotes(opc, limiar: float) -> None:
    """Uma linha por variação do pacote, da menor para a maior nota: pedido em cinza escuro, recomendado em laranja."""
    linhas = []
    for r in opc.itertuples():
        cor = DESTAQUE if r.recomendado else ("#4B5563" if r.pedido else "#D7DCE0")
        tag = ("<span style='color:%s;font-weight:700;'>recomendado</span>" % DESTAQUE if r.recomendado else
               "<span style='color:#374151;font-weight:700;'>pedido</span>" if r.pedido else "")
        peso = "700" if (r.recomendado or r.pedido) else "400"
        linhas.append(f"""
<div style="display:grid;grid-template-columns:44% 1fr 52px 84px 92px;align-items:center;gap:10px;padding:6px 0;border-top:1px solid #F0F0F0;font-size:13.5px;">
  <div style="font-weight:{peso};">{r.rotulo}</div>
  <div style="position:relative;height:14px;background:#F7F7F7;border-radius:3px;">
    <div style="position:absolute;left:0;width:{r.nota * 100:.1f}%;top:0;bottom:0;background:{cor};border-radius:3px;"></div>
    <div style="position:absolute;left:{limiar * 100:.1f}%;top:-4px;bottom:-4px;border-left:1px dashed #4B5563;"></div>
  </div>
  <div style="font-weight:{peso};text-align:right;">{virg(r.nota, 2)}</div>
  <div style="color:{TEXTO_2};text-align:right;">R$ {virg(r.mensalidade, 2)}</div>
  <div style="font-size:13px;">{tag}</div>
</div>""")
    st.markdown(f"""
<div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:0.6rem 1rem 0.5rem;">
  <div style="display:grid;grid-template-columns:44% 1fr 52px 84px 92px;gap:10px;font-size:13px;color:{TEXTO_2};padding-bottom:4px;">
    <span>CONTRATO · PAGAMENTO · EXTRAS</span><span>nota de risco no 1º mês (tracejado = limiar {virg(limiar, 2)})</span>
    <span style="text-align:right;">nota</span><span style="text-align:right;">mensalidade</span><span></span></div>
  {''.join(linhas)}
</div>""", unsafe_allow_html=True)
