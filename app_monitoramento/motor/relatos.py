"""
motor/relatos.py
Leitura do último relato registrado de cada cliente (o comentário CustomerFeedback da inferência).

O relato NÃO entra na nota do modelo (vazamento, decisão D9). Ele serve para a operação: decidir o roteiro da ligação
e a ordem da lista de contatos. A regra de saída declarada é a mesma do notebook 04 (TERMOS_CANCELAMENTO, seção 7.3b
do 03, que acerta 98,9% no histórico). Tom e motivos citados são regras de palavras, simples e explicáveis.
"""

import re

import pandas as pd

# mesma regra do notebook 04 (gold_churn_texto.fl_menciona_cancelamento)
TERMOS_CANCELAMENTO = (r"decided to churn|decided to cancel|recently canceled|recently cancelled|have canceled|switched to|"
                       r"decided to switch|decided to leave|had to churn|made the decision to churn|decision to churn")

POSITIVAS = (r"satisf(?!ied with the price)|happy|reliable|reasonable|appreciate|recommend|great|excellent|"
             r"no complaints|pleased|fair for|convenient|convenience|hassle-free|smooth|fast")
NEGATIVAS = (r"frustrat|\bhigh\b|disappoint|unhappy|dissatisf|too high|too expensive|steep|overpriced|poor|slow|unreliable|"
             r"outage|dropped|constant(ly)? (issue|problem)|not worth|better deal|cheaper|competitive|budget|"
             r"lack of|struggl|annoy|terrible|worst")

# motivos de queixa, procurados só nos trechos sem negação dos relatos negativos ou de saída declarada
MOTIVOS = {
    "Preço": r"\bhigh\b|too high|expensive|steep|overpriced|pricing|price|cheaper|better deal|budget|not worth|afford",
    "Conexão": r"slow|outage|reliab|dropped|disconnect|connection|connectivity|downtime|speed",
    "Atendimento": r"customer service|support|technician|help desk|wait time",
    "Contrato": r"commitment|locked|long-term contract|contract terms|flexib",
    "Forma de pagamento": r"inconvenient|outdated|modern payment|payment option",
    "Concorrência": r"another provider|other provider|competitor|better deal|elsewhere|new provider",
}


NEGACAO = r"\b(no|not|never|without|few|any|nothing|hardly|rarely)\b|n't"


def _conta(padrao: str, texto: str) -> int:
    return len(re.findall(padrao, texto))


QUEIXA = NEGATIVAS + r"|issue|problem|inconvenient|outdated|decided|cancel|churn|switch|wish|would have"


def _trechos(texto: str) -> list:
    return [t for t in re.split(r"[.,;!?]|\band\b|\bbut\b|\bhowever\b", texto) if t.strip()]


def _sem_negacao(texto: str) -> str:
    """Tira os trechos negados ("no issues with slow speeds", "very few outages"), para não contar como reclamação."""
    return " ".join(t for t in _trechos(texto) if not re.search(NEGACAO, t))


def _queixas(texto: str) -> str:
    """Só os trechos que trazem uma queixa ou a decisão de sair, sem negação: é onde se procuram os motivos."""
    return " ".join(t for t in _trechos(texto) if not re.search(NEGACAO, t) and re.search(QUEIXA, t))


def ler_relato(texto) -> dict:
    """Saída declarada, tom e motivos de queixa citados num relato."""
    t = str(texto or "").lower()
    decidiu = bool(re.search(TERMOS_CANCELAMENTO, t))
    pos, neg = _conta(POSITIVAS, t), _conta(NEGATIVAS, _sem_negacao(t))
    if decidiu or (neg > 0 and pos == 0):
        tom = "Negativo"
    elif pos > 0 and neg == 0:
        tom = "Positivo"
    elif pos > 0 and neg > 0:
        tom = "Misto"
    else:
        tom = "Neutro"
    queixa = _queixas(t) if tom in ("Negativo", "Misto") else ""
    motivos = [nome for nome, p in MOTIVOS.items() if re.search(p, queixa)]
    return {"decidiu_sair": int(decidiu), "tom": tom, "motivos_citados": "; ".join(motivos)}


def abordagem(decidiu_sair: int, previsto_sim: int) -> str:
    """Que conversa ter: recuperação (já disse que vai sair), retenção (risco sem decisão) ou fidelização."""
    if decidiu_sair:
        return "Recuperação"
    return "Retenção" if previsto_sim else "Fidelização"


def receptividade(decidiu_sair: int, tom: str) -> str:
    """Chance de o cliente ouvir uma oferta, pelo último relato (aproximação até existir o histórico de contatos)."""
    if decidiu_sair or tom == "Negativo":
        return "Baixa"
    return "Alta" if tom == "Positivo" else "Média"


def montar_relatos(inferencia: pd.DataFrame, previsto: pd.Series) -> pd.DataFrame:
    """Uma linha por cliente: relato, saída declarada, tom, motivos citados, abordagem e receptividade.

    inferencia: customerID e CustomerFeedback (silver_inference ou inference.csv)
    previsto:   Churn_Previsto (1/0) indexado por customerID (gold_churn_inferencia_scored)
    """
    r = inferencia[["customerID", "CustomerFeedback"]].rename(columns={"CustomerFeedback": "relato"}).copy()
    r["relato"] = r["relato"].astype(str).str.replace(r"\s*\n\s*", " ", regex=True).str.strip().str.strip('"')
    lido = pd.DataFrame([ler_relato(t) for t in r["relato"]], index=r.index)
    r = pd.concat([r, lido], axis=1)
    sim = r["customerID"].map(previsto).fillna(0).astype(int)
    r["abordagem"] = [abordagem(d, s) for d, s in zip(r["decidiu_sair"], sim)]
    r["receptividade"] = [receptividade(d, t) for d, t in zip(r["decidiu_sair"], r["tom"])]
    return r
