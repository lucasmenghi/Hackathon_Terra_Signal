"""
utils/jornada.py
Gamificação do atendimento (estilo Duolingo): meta diária, XP, nível, sequência, impacto e conquistas.

Princípio: o XP premia REGISTRAR o atendimento e seguir a escada de ofertas, não "salvar a qualquer custo".
Cada registro é o dado que falta para medir o recall real e o efeito das ofertas (notebook 09, 2.3).
Os registros ficam na sessão do navegador (st.session_state); a versão completa grava numa tabela do catálogo.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from config.theme import COR, DESTAQUE, TEXTO_2, virg

RESULTADOS = {
    "principal": "Aceitou a oferta principal",
    "alternativa": "Aceitou uma alternativa da escada",
    "recusou": "Recusou as ofertas",
    "retorno": "Pediu para ligar depois",
    "nao_atendeu": "Não atendeu",
}
ACEITOU = {"principal", "alternativa"}
XP_NIVEL = 100
FUSO = ZoneInfo("America/Sao_Paulo")          # o servidor do app roda em UTC

CONQUISTAS = {
    "primeiro": ("Primeiro atendimento", "Registrou o primeiro atendimento do dia"),
    "dificil": ("Missão difícil", "Atendeu um cliente do decil D1, os 10% de maior risco"),
    "fidelidade": ("Fidelidade longa", "Um cliente aceitou migrar para o contrato de dois anos"),
    "escada": ("Escada completa", "Três atendimentos seguidos começando pela oferta principal"),
    "s1": ("Especialista em fibra", "Atendeu 3 clientes do segmento S1"),
    "meta": ("Meta do dia", "Bateu a meta diária de contatos"),
}

# o roteiro de cada ligação: os 4 passos que a operadora marca antes de registrar (+5 XP com os 4)
PASSOS = ["Confirmei se o relato ainda vale", "Perguntei o motivo principal", "Comecei pela oferta principal",
          "Combinei o próximo passo com o cliente"]

# missões do dia: +20 XP cada, uma vez por dia
MISSOES = {
    "d1": ("Atender 2 clientes do D1", 2, lambda regs: sum(r["decil"] == 1 for r in regs)),
    "debito": ("Fechar 1 troca para débito automático", 1,
               lambda regs: sum(r["aceitou"] and "debito_automatico" in r["acoes"] for r in regs)),
    "recuperacao": ("Fazer 1 conversa de recuperação", 1, lambda regs: sum(r["abordagem"] == "Recuperação" for r in regs)),
    "roteiro": ("Completar o roteiro em 3 ligações", 3, lambda regs: sum(r["passos"] == len(PASSOS) for r in regs)),
}
XP_MISSAO = 20


def estado() -> dict:
    if "jornada" not in st.session_state:
        st.session_state["jornada"] = {"registros": [], "conquistas": [], "missoes": [], "meta": 10}
    st.session_state["jornada"].setdefault("missoes", [])
    return st.session_state["jornada"]


def registrados() -> set:
    return {r["customerID"] for r in estado()["registros"]}


def _sequencia(regs: list) -> int:
    n = 0
    for r in reversed(regs):
        if not r["seguiu_escada"]:
            break
        n += 1
    return n


def xp_do_registro(decil: int, resultado: str, seguiu_escada: bool, passos: int) -> int:
    return (10 + (5 if seguiu_escada else 0) + (10 if decil == 1 else 0) + (10 if resultado in ACEITOU else 0)
            + (5 if passos == len(PASSOS) else 0))


def registrar(cliente: dict, decil: int, resultado: str, seguiu_escada: bool, oferta: str, acoes: tuple,
              abordagem: str = "", modo: str = "", passos: int = 0, nota: str = "") -> tuple[int, list]:
    """Grava o atendimento, calcula o XP (com as missões cumpridas) e devolve (xp ganho, conquistas e missões novas)."""
    e = estado()
    xp = xp_do_registro(decil, resultado, seguiu_escada, passos)
    e["registros"].append({
        "data": datetime.now(FUSO).strftime("%d/%m/%Y"), "hora": datetime.now(FUSO).strftime("%H:%M"),
        "customerID": cliente["customerID"], "tipo": modo, "abordagem": abordagem, "segmento": cliente.get("segmento"),
        "decil": decil, "resultado": RESULTADOS[resultado], "aceitou": resultado in ACEITOU,
        "oferta": oferta if resultado in ACEITOU else "", "acoes": tuple(acoes) if resultado in ACEITOU else (),
        "contrato_2anos": resultado in ACEITOU and "contrato_2anos" in acoes, "seguiu_escada": seguiu_escada,
        "passos": passos, "anotacao": nota, "mensalidade": float(cliente["MonthlyCharges"]), "xp": xp,
    })
    regs = e["registros"]
    novas = []
    for chave, (nome, alvo, contar) in MISSOES.items():
        if chave not in e["missoes"] and contar(regs) >= alvo:
            e["missoes"].append(chave)
            regs[-1]["xp"] += XP_MISSAO
            xp += XP_MISSAO
            novas.append(f"missao:{chave}")
    testes = {
        "primeiro": len(regs) >= 1,
        "dificil": any(r["decil"] == 1 for r in regs),
        "fidelidade": any(r["contrato_2anos"] for r in regs),
        "escada": _sequencia(regs) >= 3,
        "s1": sum(r["segmento"] == "S1" for r in regs) >= 3,
        "meta": len(regs) >= e["meta"],
    }
    for chave, ok in testes.items():
        if ok and chave not in e["conquistas"]:
            e["conquistas"].append(chave)
            novas.append(chave)
    return xp, novas


def historico(customer_id: str) -> pd.DataFrame:
    """Os contatos já registrados com este cliente (hoje, nesta sessão)."""
    regs = [r for r in estado()["registros"] if r["customerID"] == customer_id]
    cols = ["data", "hora", "tipo", "abordagem", "resultado", "oferta", "anotacao"]
    return pd.DataFrame(regs, columns=list(regs[0]) if regs else cols)[cols]


def resumo() -> dict:
    e = estado()
    regs = e["registros"]
    xp = sum(r["xp"] for r in regs)
    return {"n": len(regs), "meta": e["meta"], "xp": xp, "nivel": 1 + xp // XP_NIVEL, "xp_no_nivel": xp % XP_NIVEL,
            "sequencia": _sequencia(regs), "aceites": sum(r["aceitou"] for r in regs),
            "receita_anual": sum(12 * r["mensalidade"] for r in regs if r["aceitou"])}


def _anel(feito: int, meta: int) -> str:
    frac = min(feito / max(meta, 1), 1.0)
    r, c = 34, 2 * 3.14159 * 34
    cor = DESTAQUE if frac >= 1 else COR
    return f"""
<svg width="92" height="92" viewBox="0 0 92 92">
  <circle cx="46" cy="46" r="{r}" fill="none" stroke="#E5E7EB" stroke-width="9"/>
  <circle cx="46" cy="46" r="{r}" fill="none" stroke="{cor}" stroke-width="9" stroke-linecap="round"
          stroke-dasharray="{c * frac:.1f} {c:.1f}" transform="rotate(-90 46 46)"/>
  <text x="46" y="44" text-anchor="middle" font-size="20" font-weight="700" fill="#1A1A1A">{feito}</text>
  <text x="46" y="61" text-anchor="middle" font-size="12" fill="{TEXTO_2}">de {meta}</text>
</svg>"""


def painel_lateral():
    """Barra lateral: meta do dia (anel), nível e XP, sequência, impacto e conquistas."""
    e = estado()
    s = resumo()
    with st.sidebar:
        st.markdown(f"""
<div style="background:#fff;border:1px solid #E5E7EB;border-radius:12px;padding:0.8rem 0.9rem;margin-top:0.4rem;">
  <p style="font-size:12.5px;font-weight:700;color:{TEXTO_2};text-transform:uppercase;letter-spacing:0.06em;margin:0 0 6px;">Sua jornada hoje</p>
  <div style="display:flex;align-items:center;gap:12px;">
    {_anel(s['n'], s['meta'])}
    <div style="font-size:13px;line-height:1.5;color:#1A1A1A;">
      <b>Meta do dia</b><br><span style="color:{TEXTO_2};">contatos da fila registrados</span><br>
      <b style="color:{DESTAQUE if s['sequencia'] >= 3 else COR};">Sequência: {s['sequencia']}</b>
      <span style="color:{TEXTO_2};"> na escada</span>
    </div>
  </div>
  <p style="font-size:13px;margin:10px 0 3px;"><b>Nível {s['nivel']}</b> · {s['xp']} XP</p>
  <div style="height:8px;background:#E5E7EB;border-radius:4px;">
    <div style="width:{s['xp_no_nivel']}%;height:8px;background:{COR};border-radius:4px;"></div></div>
  <p style="font-size:12.5px;color:{TEXTO_2};margin:3px 0 8px;">faltam {XP_NIVEL - s['xp_no_nivel']} XP para o nível {s['nivel'] + 1}</p>
  <p style="font-size:13px;margin:0;"><b>{s['aceites']}</b> {'oferta aceita' if s['aceites'] == 1 else 'ofertas aceitas'} ·
     <b>R$ {virg(s['receita_anual'], 0)}</b> por ano em mensalidades mantidas</p>
</div>""", unsafe_allow_html=True)
        regs = e["registros"]
        linhas = ""
        for chave, (nome, alvo, contar) in MISSOES.items():
            feito = min(contar(regs), alvo)
            ok = chave in e["missoes"]
            cor = DESTAQUE if ok else COR
            linhas += (f'<div style="margin:0 0 7px;"><div style="display:flex;justify-content:space-between;font-size:13px;'
                       f'color:#1A1A1A;"><span>{"✓ " if ok else ""}{nome}</span><b>{feito}/{alvo}</b></div>'
                       f'<div style="height:6px;background:#E5E7EB;border-radius:3px;margin-top:3px;">'
                       f'<div style="width:{100 * feito / alvo:.0f}%;height:6px;background:{cor};border-radius:3px;"></div></div></div>')
        st.markdown(f'<p style="font-size:12.5px;font-weight:700;color:{TEXTO_2};text-transform:uppercase;letter-spacing:0.06em;'
                    f'margin:0.9rem 0 6px;">Missões do dia · +{XP_MISSAO} XP cada</p>{linhas}', unsafe_allow_html=True)
        ganhas = [CONQUISTAS[c][0] for c in e["conquistas"]]
        faltam = [CONQUISTAS[c][0] for c in CONQUISTAS if c not in e["conquistas"]]
        selos = "".join(f'<span style="display:inline-block;background:#FBEFE3;color:#8A4B12;font-size:12.5px;font-weight:600;'
                        f'padding:3px 9px;border-radius:12px;margin:0 4px 5px 0;">{g}</span>' for g in ganhas)
        apagados = "".join(f'<span style="display:inline-block;background:#F3F4F6;color:{TEXTO_2};font-size:12.5px;'
                           f'padding:3px 9px;border-radius:12px;margin:0 4px 5px 0;">{f}</span>' for f in faltam)
        st.markdown(f'<p style="font-size:12.5px;font-weight:700;color:{TEXTO_2};text-transform:uppercase;letter-spacing:0.06em;'
                    f'margin:0.9rem 0 4px;">Conquistas · {len(ganhas)} de {len(CONQUISTAS)}</p>{selos}{apagados}',
                    unsafe_allow_html=True)
        e["meta"] = int(st.number_input("Meta diária de contatos", min_value=1, max_value=50, value=e["meta"], step=1))
        if e["registros"]:
            df = pd.DataFrame(e["registros"]).drop(columns=["acoes"], errors="ignore")
            st.download_button("Baixar os registros (CSV)", df.to_csv(index=False).encode("utf-8"),
                               file_name=f"atendimentos_{datetime.now(FUSO):%Y%m%d}.csv", mime="text/csv",
                               help="Estes registros são o dado que mede o recall real e o efeito das ofertas")


def comemorar(xp: int, novas: list, meta_batida_agora: bool):
    st.toast(f"+{xp} XP · atendimento registrado")
    for c in novas:
        if c.startswith("missao:"):
            st.toast(f"Missão cumprida: {MISSOES[c.split(':', 1)[1]][0]} · +{XP_MISSAO} XP")
            continue
        nome, desc = CONQUISTAS[c]
        st.toast(f"Conquista: {nome}. {desc}")
    if meta_batida_agora:
        st.balloons()
