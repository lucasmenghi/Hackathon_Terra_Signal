"""A conta do modelo oficial (logística Lasso do notebook 06), feita à mão a partir dos parâmetros exportados.

Probabilidade = 1 ÷ (1 + e^−(intercepto + Σ coeficiente × variável padronizada)). O notebook 10 exporta os
parâmetros do modelo registrado no MLflow e confere que esta conta devolve as mesmas notas publicadas.
"""
import json
from itertools import combinations

import numpy as np
import pandas as pd

from .abt import montar_abt

# temas para explicar a nota: cada coluna do modelo pertence a um "motivo"
TEMAS = {
    "Tempo de casa": ["tenure", "TenureCohort_", "is_new_customer", "new_monthly_customer"],
    "Tipo de contrato": ["Contract_", "IsHighRiskContract"],
    "Forma de pagamento": ["PaymentMethod_", "pagamento_automatico", "PaperlessBilling_"],
    "Suporte e proteção": ["OnlineSecurity_bin", "OnlineBackup_bin", "DeviceProtection_bin", "TechSupport_bin",
                           "no_support_with_internet", "HasFiberOpticWithoutTechSupport", "n_protecao"],
    "Pacote e preço": ["InternetService_", "MultipleLines_", "StreamingTV_bin", "StreamingMovies_bin", "n_streaming",
                       "TotalServicesSubscribed", "MonthlyCharges", "mensalidade_relativa_pacote"],
    "Histórico de cobrança": ["TotalCharges", "fl_total_charges_ausente", "ChargesRatio", "charge_difference"],
    "Perfil": ["SeniorCitizen", "Partner_", "Dependents_", "has_family", "MonthlyIncome", "IncomeCommitment"],
}

# ações de retenção que a operadora pode oferecer (mudança no cadastro, mensalidade igual = cortesia)
ACOES = {
    "contrato_anual": {"rotulo": "Migrar para contrato anual", "campo": "Contract", "novo": "One year",
                       "vale": lambda c: c["Contract"] == "Month-to-month", "grupo": "contrato",
                       "vale_lote": lambda d: d["Contract"].eq("Month-to-month"),
                       "fala": "Oferecer o plano anual com desconto nos primeiros meses, mantendo o que ele já tem."},
    "contrato_2anos": {"rotulo": "Migrar para contrato de dois anos", "campo": "Contract", "novo": "Two year",
                       "vale": lambda c: c["Contract"] != "Two year", "grupo": "contrato",
                       "vale_lote": lambda d: d["Contract"].ne("Two year"),
                       "fala": "Oferecer o plano de dois anos com o melhor preço da tabela e a mensalidade congelada."},
    "debito_automatico": {"rotulo": "Trocar para débito automático", "campo": "PaymentMethod", "novo": "Bank transfer (automatic)",
                          "vale": lambda c: c["PaymentMethod"] in ("Electronic check", "Mailed check"), "grupo": "pagamento",
                          "vale_lote": lambda d: d["PaymentMethod"].isin(["Electronic check", "Mailed check"]),
                          "fala": "Oferecer um desconto na fatura para trocar o cheque por débito automático."},
    "suporte": {"rotulo": "Incluir suporte técnico", "campo": "TechSupport", "novo": "Yes",
                "vale": lambda c: c["InternetService"] != "No" and c["TechSupport"] == "No", "grupo": "suporte",
                "vale_lote": lambda d: d["InternetService"].ne("No") & d["TechSupport"].eq("No"),
                "fala": "Incluir o suporte técnico sem custo por 3 meses, com um técnico de referência."},
    "seguranca": {"rotulo": "Incluir segurança online", "campo": "OnlineSecurity", "novo": "Yes",
                  "vale": lambda c: c["InternetService"] != "No" and c["OnlineSecurity"] == "No", "grupo": "seguranca",
                  "vale_lote": lambda d: d["InternetService"].ne("No") & d["OnlineSecurity"].eq("No"),
                  "fala": "Incluir a segurança online sem custo por 3 meses."},
}

NOMES_PAGAMENTO = {"Electronic check": "cheque eletrônico", "Mailed check": "boleto pelo correio",
                   "Bank transfer (automatic)": "débito automático", "Credit card (automatic)": "cartão de crédito automático"}
NOMES_CONTRATO = {"Month-to-month": "mensal", "One year": "anual", "Two year": "de dois anos"}
NOMES_INTERNET = {"Fiber optic": "fibra", "DSL": "DSL", "No": "sem internet"}


class Motor:
    def __init__(self, parametros: dict):
        self.p = parametros
        self.colunas = parametros["colunas"]
        self.categoricas = parametros["categoricas"]
        self.mediana = np.array(parametros["mediana"])
        self.media = np.array(parametros["media"])
        self.escala = np.array(parametros["escala"])
        self.coef = np.array(parametros["coeficientes"])
        self.intercepto = float(parametros["intercepto"])
        self.limiar = float(parametros["limiar"])
        self.media_pacote = parametros["media_pacote"]
        self.cortes_decil = np.array(parametros["cortes_decil"])        # 9 cortes, do maior risco para o menor
        self.preco = parametros["preco"]
        self.tema_coluna = {c: next((t for t, pref in TEMAS.items() if any(c == p or (p.endswith("_") and c.startswith(p)) for p in pref)), "Outros")
                            for c in self.colunas}

    @classmethod
    def carregar(cls, caminho: str) -> "Motor":
        with open(caminho, encoding="utf-8") as f:
            return cls(json.load(f))

    # ---------- da ficha do cliente às 41 colunas ----------
    def matriz(self, abt: pd.DataFrame) -> pd.DataFrame:
        X = pd.DataFrame(index=abt.index)
        for col in self.colunas:
            if col in abt.columns and pd.api.types.is_numeric_dtype(abt[col]):
                X[col] = pd.to_numeric(abt[col], errors="coerce")
                continue
            var = next((v for v in self.categoricas if col.startswith(v + "_")), None)
            X[col] = abt[var].astype(str).eq(col[len(var) + 1:]).astype(float) if var else 0.0
        return X.replace([np.inf, -np.inf], np.nan).astype(float)

    def padronizar(self, ficha: pd.DataFrame) -> np.ndarray:
        X = self.matriz(montar_abt(ficha, self.media_pacote)).to_numpy()
        X = np.where(np.isnan(X), self.mediana, X)
        return (X - self.media) / self.escala

    def probabilidade(self, ficha: pd.DataFrame) -> np.ndarray:
        z = self.padronizar(ficha) @ self.coef + self.intercepto
        return 1 / (1 + np.exp(-z))

    def prob1(self, cliente: dict) -> float:
        return float(self.probabilidade(pd.DataFrame([cliente]))[0])

    # ---------- leitura da nota ----------
    def decil(self, p: float) -> int:
        """1 = 10% de maior risco da carteira; 10 = 10% de menor risco."""
        return int(1 + np.sum(p < self.cortes_decil))

    @staticmethod
    def faixa(decil: int) -> str:
        return "Alto" if decil <= 2 else "Médio" if decil <= 5 else "Baixo"

    def motivos(self, cliente: dict) -> pd.DataFrame:
        """Quanto cada tema empurra a nota para cima (+) ou para baixo (−), em relação a um cliente médio do treino."""
        contrib = self.padronizar(pd.DataFrame([cliente]))[0] * self.coef
        s = pd.Series(contrib, index=self.colunas).groupby(self.tema_coluna).sum()
        out = s.rename("efeito").to_frame()
        out["descricao"] = [descrever(t, cliente) for t in out.index]
        return out.sort_values("efeito", ascending=False)

    # ---------- ofertas ----------
    def preco_estimado(self, cliente: dict) -> float:
        p = self.preco
        v = p["intercepto"]
        v += p["telefone"] * (cliente["PhoneService"] == "Yes") + p["linhas_multiplas"] * (cliente["MultipleLines"] == "Yes")
        v += p["dsl"] * (cliente["InternetService"] == "DSL") + p["fibra"] * (cliente["InternetService"] == "Fiber optic")
        for s in ["OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies"]:
            v += p[s] * (cliente[s] == "Yes")
        return float(v)

    def aplicar(self, cliente: dict, acoes) -> dict:
        novo = dict(cliente)
        for a in acoes:
            novo[ACOES[a]["campo"]] = ACOES[a]["novo"]
        return novo

    def acoes_validas(self, cliente: dict) -> list:
        return [a for a, d in ACOES.items() if d["vale"](cliente)]

    def ofertas(self, cliente: dict, max_acoes: int = 2) -> pd.DataFrame:
        """Cada ação sozinha e cada par de ações (sem repetir o mesmo tipo), com a nota depois da oferta."""
        base = self.prob1(cliente)
        validas = self.acoes_validas(cliente)
        linhas = []
        for k in range(1, max_acoes + 1):
            for combo in combinations(validas, k):
                if len({ACOES[a]["grupo"] for a in combo}) < k:
                    continue
                p = self.prob1(self.aplicar(cliente, combo))
                linhas.append({"acoes": combo, "oferta": " + ".join(ACOES[a]["rotulo"] for a in combo),
                               "n_acoes": k, "nota_antes": base, "nota_depois": p, "reducao": base - p,
                               "decil_depois": self.decil(p)})
        cols = ["acoes", "oferta", "n_acoes", "nota_antes", "nota_depois", "reducao", "decil_depois"]
        return pd.DataFrame(linhas, columns=cols).sort_values("nota_depois").reset_index(drop=True)

    def ofertas_em_lote(self, fichas: pd.DataFrame, max_acoes: int = 2) -> pd.DataFrame:
        """Para muitos clientes de uma vez: a nota antes e depois de cada oferta válida (uma linha por cliente e oferta)."""
        fichas = fichas.reset_index(drop=True)
        base = self.probabilidade(fichas)
        combos = [c for k in range(1, max_acoes + 1) for c in combinations(ACOES, k)
                  if len({ACOES[a]["grupo"] for a in c}) == k]
        partes = []
        for combo in combos:
            ok = np.logical_and.reduce([ACOES[a]["vale_lote"](fichas).to_numpy() for a in combo])
            if not ok.any():
                continue
            sub = fichas.loc[ok].copy()
            for a in combo:
                sub[ACOES[a]["campo"]] = ACOES[a]["novo"]
            p = self.probabilidade(sub)
            partes.append(pd.DataFrame({"customerID": sub["customerID"].to_numpy(), "acoes": [combo] * len(sub),
                                        "oferta": " + ".join(ACOES[a]["rotulo"] for a in combo), "n_acoes": len(combo),
                                        "nota_antes": base[ok], "nota_depois": p}))
        out = pd.concat(partes, ignore_index=True)
        out["reducao"] = out["nota_antes"] - out["nota_depois"]
        return out


def descrever(tema: str, c: dict) -> str:
    """Frase curta, com os dados do próprio cliente, para cada tema."""
    tn = int(c["tenure"])
    if tema == "Tempo de casa":
        return f"cliente há {tn} {'mês' if tn == 1 else 'meses'}"
    if tema == "Tipo de contrato":
        return f"contrato {NOMES_CONTRATO.get(c['Contract'], c['Contract'])}"
    if tema == "Forma de pagamento":
        return f"paga por {NOMES_PAGAMENTO.get(c['PaymentMethod'], c['PaymentMethod'])}" + (", fatura digital" if c["PaperlessBilling"] == "Yes" else "")
    if tema == "Suporte e proteção":
        if c["InternetService"] == "No":
            return "não tem internet"
        faltam = [n for k, n in [("TechSupport", "suporte técnico"), ("OnlineSecurity", "segurança online")] if c[k] != "Yes"]
        return "sem " + " e sem ".join(faltam) if faltam else "tem suporte e segurança"
    if tema == "Pacote e preço":
        return f"{NOMES_INTERNET.get(c['InternetService'], c['InternetService'])}, mensalidade de R$ {c['MonthlyCharges']:.2f}".replace(".", ",")
    if tema == "Histórico de cobrança":
        return "cobranças coerentes com o plano" if not c.get("fl_total_charges_ausente") else "total cobrado ausente no cadastro"
    if tema == "Perfil":
        partes = ["idoso" if c["SeniorCitizen"] == 1 else "não idoso",
                  "com família" if (c["Partner"] == "Yes" or c["Dependents"] == "Yes") else "sem parceiro nem dependentes"]
        return ", ".join(partes)
    return ""


def novo_cliente(perfil: dict, pacote: dict, motor: Motor) -> dict:
    """Ficha de um cliente que ainda não existe: primeiro mês (tenure = 1), mensalidade pela tabela de preço."""
    internet = pacote["internet"]
    tem_net = internet != "No"
    c = {
        "customerID": "NOVO", "gender": "Female", "SeniorCitizen": int(perfil["idoso"]),
        "Partner": "Yes" if perfil["parceiro"] else "No", "Dependents": "Yes" if perfil["dependentes"] else "No",
        "tenure": 1, "PhoneService": "Yes" if pacote["telefone"] else "No",
        "MultipleLines": ("Yes" if pacote["linhas_multiplas"] else "No") if pacote["telefone"] else "No phone service",
        "InternetService": internet, "Contract": pacote["contrato"], "PaperlessBilling": "Yes" if pacote["fatura_digital"] else "No",
        "PaymentMethod": pacote["pagamento"], "MonthlyIncome": float(perfil.get("renda") or motor.p["renda_mediana"]),
        "fl_total_charges_ausente": 0,
    }
    for s in ["OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies"]:
        c[s] = ("Yes" if pacote.get(s) else "No") if tem_net else "No internet service"
    c["MonthlyCharges"] = motor.preco_estimado(c)
    c["TotalCharges"] = c["MonthlyCharges"]           # primeiro mês
    return c
