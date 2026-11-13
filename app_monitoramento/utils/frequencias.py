"""
utils/frequencias.py
As variáveis-chave do cliente em frequência natural ("4 em cada 10 saem"), para a operadora e para a banca.

As taxas são de saída observada nos 5.634 clientes do histórico (gold_churn_treino; notebooks 03 e 05). O risco do
próprio cliente usa a taxa real do decil dele no teste (ganho_teste.csv, notebook 10, 5.2), e não a nota do modelo.
"""

import streamlit as st

from config.theme import COR, DESTAQUE, TEXTO_2

CONTRATO = {"Month-to-month": 0.427, "One year": 0.116, "Two year": 0.033}
TEMPO = [(6, 0.523, "até 6 meses"), (12, 0.354, "7 a 12 meses"), (24, 0.286, "1 a 2 anos"), (48, 0.219, "2 a 4 anos"),
         (999, 0.095, "mais de 4 anos")]
PAGAMENTO = {"Electronic check": 0.451, "Mailed check": 0.194, "Bank transfer (automatic)": 0.172,
             "Credit card (automatic)": 0.156}
SEM_INTERNET = 0.072
PROTECAO = {("Fiber optic", False): 0.493, ("Fiber optic", True): 0.229, ("DSL", False): 0.418, ("DSL", True): 0.153}
NOME_CONTRATO = {"Month-to-month": "Contrato mensal", "One year": "Contrato anual", "Two year": "Contrato de dois anos"}
NOME_PAGAMENTO = {"Electronic check": "Cheque eletrônico", "Mailed check": "Boleto pelo correio",
                  "Bank transfer (automatic)": "Débito automático", "Credit card (automatic)": "Cartão automático"}


def em_10(taxa: float) -> str:
    """Taxa → frequência natural: 0,427 → 'mais de 4 em cada 10'; 0,761 → 'quase 8 em cada 10'; 0,033 → '3 em cada 100'."""
    if taxa < 0.05:
        return f"{max(1, round(100 * taxa))} em cada 100"
    x = 10 * taxa
    n = round(x)
    if n == 0:
        return "menos de 1 em cada 10"
    prefixo = "quase " if x < n - 0.2 else "mais de " if x > n + 0.2 else ""
    return f"{prefixo}{n} em cada 10"


def _tempo(meses: int):
    for teto, taxa, rotulo in TEMPO:
        if meses <= teto:
            return taxa, rotulo
    return TEMPO[-1][1], TEMPO[-1][2]


def variaveis_chave(c: dict) -> list:
    """(variável, situação do cliente, taxa de saída de clientes iguais, ação) para as quatro variáveis-chave."""
    meses = int(c["tenure"])
    t_tempo, faixa = _tempo(meses)
    tem_net = c["InternetService"] != "No"
    suporte = c.get("TechSupport") == "Yes"
    if tem_net:
        t_prot = PROTECAO[(c["InternetService"], suporte)]
        sit_prot = f"{'Fibra' if c['InternetService'] == 'Fiber optic' else 'DSL'} {'com' if suporte else 'sem'} suporte técnico"
        acao_prot = "mantenha o suporte" if suporte else "ofereça suporte ou segurança por cortesia"
    else:
        t_prot, sit_prot, acao_prot = SEM_INTERNET, "Sem internet", "ofereça internet só se ele pedir"
    contrato, pag = c["Contract"], c["PaymentMethod"]
    return [
        ("Contrato", NOME_CONTRATO[contrato], CONTRATO[contrato],
         {"Month-to-month": "ofereça o contrato anual", "One year": "ofereça o de dois anos na renovação",
          "Two year": "cliente fidelizado"}[contrato]),
        ("Tempo de casa", f"{meses} {'mês' if meses == 1 else 'meses'} ({faixa})", t_tempo,
         "combine o acompanhamento dos primeiros meses" if meses <= 12 else "reconheça o tempo de casa"),
        ("Proteção", sit_prot, t_prot, acao_prot),
        ("Pagamento", NOME_PAGAMENTO[pag], PAGAMENTO[pag],
         "ofereça desconto no débito automático" if pag in ("Electronic check", "Mailed check") else "pagamento já automático"),
    ]


def resumo_cliente(c: dict, taxa_decil: float, decil: int, conversa: str, oferta: str):
    """O contexto do cliente numa tela: risco em frequência natural, as quatro variáveis-chave, a conversa e a oferta."""
    def cor(t):
        return DESTAQUE if t >= 0.35 else COR if t <= 0.15 else "#1A1A1A"
    tiles = "".join(f"""
<div style="flex:1;min-width:190px;border:1px solid #E5E7EB;border-radius:10px;padding:0.7rem 0.8rem;background:#fff;">
  <p style="font-size:12.5px;font-weight:700;color:{TEXTO_2};text-transform:uppercase;letter-spacing:0.05em;margin:0;">{nome}</p>
  <p style="font-size:14.5px;font-weight:600;color:#1A1A1A;margin:3px 0 2px;">{sit}</p>
  <p style="font-size:14px;color:{cor(t)};font-weight:700;margin:0 0 4px;">{em_10(t).capitalize()} saem</p>
  <p style="font-size:13px;color:#1A1A1A;margin:0;">→ {acao}</p>
</div>""" for nome, sit, t, acao in variaveis_chave(c))
    st.markdown(f"""
<div style="background:#F9FAFB;border:1px solid #E5E7EB;border-left:5px solid {cor(taxa_decil)};border-radius:12px;padding:0.9rem 1rem;margin:0.6rem 0 0.4rem;">
  <p style="font-size:12.5px;font-weight:700;color:{TEXTO_2};text-transform:uppercase;letter-spacing:0.06em;margin:0;">Resumo do cliente</p>
  <p style="font-size:1.25rem;font-weight:700;color:#1A1A1A;margin:2px 0 2px;">Clientes como ele: {em_10(taxa_decil)} saíram</p>
  <p style="font-size:13.5px;color:{TEXTO_2};margin:0 0 10px;">Grupo de risco {decil} de 10 (D{decil}), pela taxa real de saída desse grupo nos clientes de teste ·
     conversa: <b style="color:#1A1A1A;">{conversa}</b> · oferta principal: <b style="color:#1A1A1A;">{oferta}</b></p>
  <div style="display:flex;gap:10px;flex-wrap:wrap;">{tiles}</div>
</div>""", unsafe_allow_html=True)
