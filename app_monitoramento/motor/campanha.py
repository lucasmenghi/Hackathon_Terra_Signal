"""Simulador de campanha de retenção: quantos clientes contatar para ter o maior retorno.

Usa a taxa REAL de churn de cada decil no teste (notebook 10, ganho_teste.csv), e não a nota do modelo, que é inflada
pelo balanceamento (no D1, nota média 0,89 para 76% de churn real).

Para cada cliente contatado, com taxa de churn t, mensalidade m, aceite a, desconto d e horizonte H meses:
- valor mantido   = t × a × m × (1 − d) × H        (quem ia sair, aceitou e ficou pagando com desconto)
- custo do desconto para quem ficaria de qualquer jeito = (1 − t) × a × m × d × H
- custo do contato = c
Vale contatar enquanto o valor mantido supera os dois custos. Igualando, a nota de corte em taxa real é
t* = (c + a·m·d·H) ÷ (a·m·H), a regra p* = custo ÷ (sucesso × valor) do notebook 00 com o desconto incluído.
"""

import numpy as np
import pandas as pd


def taxa_por_cliente(clientes: pd.DataFrame, ganho: pd.DataFrame) -> pd.Series:
    """Taxa real de churn do decil de cada cliente (D1 = maior risco), medida no teste."""
    taxa = dict(zip(ganho["decil"].astype(int), ganho["taxa_churn"].astype(float)))
    return clientes["Decil_Risco"].astype(str).str.lstrip("D").astype(int).map(taxa)


def simular(clientes: pd.DataFrame, ganho: pd.DataFrame, custo: float, aceite: float, desconto: float,
            horizonte: int) -> pd.DataFrame:
    """Uma linha por tamanho de campanha (contatando os n de maior nota): valor, custos e lucro acumulados."""
    d = clientes.sort_values("Probabilidade_Churn", ascending=False).reset_index(drop=True)
    t = taxa_por_cliente(d, ganho).to_numpy()
    m = d["MonthlyCharges"].to_numpy(float)
    valor = t * aceite * m * (1 - desconto) * horizonte
    custo_desc = (1 - t) * aceite * m * desconto * horizonte
    custo_cont = np.full(len(d), custo)
    out = pd.DataFrame({
        "n": np.arange(1, len(d) + 1),
        "nota": d["Probabilidade_Churn"].to_numpy(),
        "valor_mantido": valor.cumsum(),
        "custo_desconto": custo_desc.cumsum(),
        "custo_contato": custo_cont.cumsum(),
        "clientes_mantidos": (t * aceite).cumsum(),
        "churners_contatados": t.cumsum(),
    })
    out["lucro"] = out["valor_mantido"] - out["custo_desconto"] - out["custo_contato"]
    out["pct_carteira"] = out["n"] / len(d)
    out = pd.concat([pd.DataFrame([{c: 0.0 for c in out.columns}]), out], ignore_index=True)
    out.loc[0, "nota"] = 1.0
    return out


def corte_em_taxa(custo: float, aceite: float, desconto: float, horizonte: int, mensalidade: float) -> float:
    """Taxa real de churn mínima para valer o contato, para uma mensalidade (regra do notebook 00 com desconto)."""
    if aceite <= 0 or mensalidade <= 0:
        return float("inf")
    return (custo + aceite * mensalidade * desconto * horizonte) / (aceite * mensalidade * horizonte)
