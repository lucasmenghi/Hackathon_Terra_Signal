"""As variáveis derivadas da ABT: as mesmas fórmulas da função montar_abt do notebook 04 (seção 2.1).

O notebook 10 confere que esta função, aplicada à silver, devolve exatamente a gold. Se o 04 mudar, mudar aqui também.
"""
import numpy as np
import pandas as pd

SERVICOS = ["OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies"]
PROTECAO = SERVICOS[:4]


def montar_abt(df: pd.DataFrame, media_pacote: dict) -> pd.DataFrame:
    d = df.drop(columns=["CustomerFeedback"], errors="ignore").copy()   # D9: o texto não entra
    tn, mc, tc, renda = d["tenure"], d["MonthlyCharges"], d["TotalCharges"], d["MonthlyIncome"]
    sim = lambda c: d[c].eq("Yes")
    mensal = d["Contract"].eq("Month-to-month")
    media_mensal = (tc / tn.where(tn > 0)).fillna(mc)
    esperado = tn * mc

    for c in SERVICOS:
        d[f"{c}_bin"] = sim(c).astype(int)
    novas = {
        "IncomeCommitment": mc / renda,
        "ChargesRatio": (tc / esperado.where(esperado > 0)).fillna(1.0),
        "TotalServicesSubscribed": sum(sim(c).astype(int) for c in SERVICOS + ["PhoneService"]),
        "HasFiberOpticWithoutTechSupport": (d["InternetService"].eq("Fiber optic") & d["TechSupport"].eq("No")).astype(int),
        "IsHighRiskContract": (mensal & d["PaymentMethod"].eq("Electronic check")).astype(int),
        "TenureCohort": pd.cut(tn, [-1, 5, 12, 24, np.inf], labels=["0-5", "6-12", "13-24", "25+"]).astype(str),
        "tenure_years": tn / 12,
        "is_new_customer": (tn <= 6).astype(int),
        "tenure_group": pd.cut(tn, [-1, 6, 12, 24, 48, np.inf], labels=["0-6", "7-12", "13-24", "25-48", "49+"]).astype(str),
        "income_after_charges": renda - mc,
        "average_monthly_charges": media_mensal,
        "charge_difference": mc - media_mensal,
        "total_addons": sum(sim(c).astype(int) for c in SERVICOS),
        "has_family": (sim("Partner") | sim("Dependents")).astype(int),
        "no_support_with_internet": (d["InternetService"].ne("No") & d["TechSupport"].eq("No")).astype(int),
        "is_monthly_contract": mensal.astype(int),
        "is_electronic_check": d["PaymentMethod"].eq("Electronic check").astype(int),
        "new_monthly_customer": ((tn <= 6) & mensal).astype(int),
        "n_protecao": sum(sim(c).astype(int) for c in PROTECAO),
        "n_streaming": sim("StreamingTV").astype(int) + sim("StreamingMovies").astype(int),
        "pagamento_automatico": d["PaymentMethod"].str.contains("automatic").astype(int),
        "mensalidade_relativa_pacote": mc / d["InternetService"].map(media_pacote),
    }
    for nome, valores in novas.items():
        d[nome] = valores
    return d
