"""Usado pelo notebook 10: transforma o modelo registrado no MLflow e a gold nos parâmetros do motor (JSON)."""
import numpy as np
import pandas as pd

from .abt import SERVICOS


def parametros_do_modelo(pipeline, colunas, categoricas, limiar, prob_carteira, treino) -> dict:
    """pipeline = o pipeline de produção do 06 (passo 'limpeza' + passo 'modelo' com imputer, scaler e logística)."""
    modelo = pipeline.named_steps["modelo"]
    imp, esc, log = modelo.named_steps["imputer"], modelo.named_steps["scaler"], modelo.named_steps["modelo"]
    return {
        "colunas": list(colunas), "categoricas": list(categoricas),
        "mediana": imp.statistics_.tolist(), "media": esc.mean_.tolist(), "escala": esc.scale_.tolist(),
        "coeficientes": log.coef_[0].tolist(), "intercepto": float(log.intercept_[0]), "limiar": float(limiar),
        "media_pacote": treino.groupby("InternetService")["MonthlyCharges"].mean().to_dict(),
        "cortes_decil": np.quantile(np.asarray(prob_carteira), np.linspace(0.9, 0.1, 9)).tolist(),
        "renda_mediana": float(treino["MonthlyIncome"].median()),
    }


def tabela_de_preco(treino: pd.DataFrame):
    """Mensalidade ≈ intercepto + preço de cada item do pacote (regressão linear no treino). Devolve (preços, R²)."""
    from sklearn.linear_model import LinearRegression
    X = pd.DataFrame({"telefone": treino["PhoneService"].eq("Yes"), "linhas_multiplas": treino["MultipleLines"].eq("Yes"),
                      "dsl": treino["InternetService"].eq("DSL"), "fibra": treino["InternetService"].eq("Fiber optic"),
                      **{s: treino[s].eq("Yes") for s in SERVICOS}}).astype(float)
    reg = LinearRegression().fit(X, treino["MonthlyCharges"])
    precos = {"intercepto": float(reg.intercept_), **{c: float(v) for c, v in zip(X.columns, reg.coef_)}}
    return precos, float(reg.score(X, treino["MonthlyCharges"]))
