"""
utils/acoes.py
Do semáforo à ação: para cada indicador aceso, o que fazer, quem faz e em que notebook.
As regras são as da seção 6 do notebook 09 (Quando retreinar).
"""

import pandas as pd

NUCLEO = {"Tipo de contrato", "Tempo de casa (meses)", "Tipo de internet", "Forma de pagamento"}
PRIORIDADE = {"Parar": 0, "Retreinar": 1, "Investigar": 2, "Acompanhar": 3, "Aguardar": 4}


def _acao(r) -> tuple | None:
    """(tipo, o que fazer, quem, onde) para um indicador; None quando não há nada a fazer."""
    ind, st = r["indicador"], r["status"]
    if st == "estável":
        return None
    if ind == "Reprodução pelo MLflow":
        if st == "alerta":
            return ("Parar", "As notas publicadas diferem do modelo registrado: não usar a fila até republicar as notas pelo 06.",
                    "Dados", "06, seção 6")
        return ("Investigar", "O modelo do MLflow não foi lido nesta execução: rodar a 1.2 do 09 com acesso ao MLflow.",
                "Dados", "09, 1.2")
    if r["grupo"] == "Qualidade dos dados":
        return ("Parar", f"{ind} no lote: corrigir a carga antes de pontuar.", "Dados", "01 e 02")
    if r["grupo"] == "Desempenho real":
        if st == "aguardando":
            return ("Aguardar", f"{ind}: quando a empresa souber quem do lote saiu, preencher o churn real e medir.",
                    "Retenção + Dados", "09, 2.3")
        return ("Retreinar", f"{ind} abaixo do teste: retreinar com os dados novos e rever o limiar.", "Dados", "04, 05 e 06")
    if ind == "Taxa de Yes":
        if st == "alerta":
            return ("Investigar", "A fila de retenção mudou de tamanho além da tolerância: ver nas variáveis o que mudou e "
                    "ajustar a capacidade da central ao novo tamanho da fila.", "Retenção + Dados", "09, seção 2")
        return ("Acompanhar", "A taxa de Yes se afastou do teste: acompanhar no próximo lote.", "Dados", "09")
    if ind == "PSI das notas":
        return ("Investigar" if st == "alerta" else "Acompanhar",
                "A distribuição das notas mudou: ver quais variáveis de entrada acenderam.", "Dados", "Deriva das variáveis")
    if ind.startswith("Segmento"):
        return ("Investigar" if st == "alerta" else "Acompanhar",
                "O peso dos segmentos na carteira mudou: rodar o 07 de novo e avisar a retenção, porque as ofertas por "
                "segmento mudam junto.", "Retenção + Dados", "07")
    if ind == "Mensalidade (R$)":
        return ("Retreinar" if st == "alerta" else "Investigar",
                "A mensalidade mudou: conferir se houve reajuste ou novo plano. Se sim, retreinar e refazer a tabela de "
                "preço do atendimento.", "Dados", "06 e 10")
    if ind in NUCLEO:
        if st == "alerta":
            return ("Retreinar", f"{ind} mudou muito: é variável do núcleo do modelo. Retreinar com o histórico atualizado.",
                    "Dados", "04, 05 e 06")
        return ("Acompanhar", f"{ind} começou a mudar: conferir se veio de campanha ou mudança comercial e acompanhar.",
                "Dados", "09")
    return ("Acompanhar", f"{ind} mudou: acompanhar no próximo lote.", "Dados", "09")


def acoes_do_lote(ind: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for _, r in ind.iterrows():
        a = _acao(r)
        if a:
            linhas.append({"tipo": a[0], "indicador": r["indicador"], "status": r["status"], "o_que_fazer": a[1],
                           "quem": a[2], "onde": a[3]})
    df = pd.DataFrame(linhas, columns=["tipo", "indicador", "status", "o_que_fazer", "quem", "onde"])
    return df.assign(p=df["tipo"].map(PRIORIDADE)).sort_values("p").drop(columns="p").reset_index(drop=True)


def veredito(acoes: pd.DataFrame) -> tuple[str, str, str]:
    """(status do semáforo, título, frase) do lote inteiro, pela ação mais grave."""
    tipos = set(acoes["tipo"])
    if "Parar" in tipos:
        return "alerta", "Parar: não usar as notas deste lote", "Há um problema de dados ou de modelo que precisa ser corrigido antes."
    if "Retreinar" in tipos:
        return "alerta", "Retreinar o modelo", "A carteira mudou no que o modelo mais usa; as notas tendem a piorar."
    if "Investigar" in tipos:
        return "atenção", "Investigar antes de agir", "Algo mudou na carteira; usar a fila com cuidado até entender o quê."
    if "Acompanhar" in tipos:
        return "atenção", "Seguir, acompanhando", "Pequenas mudanças: o modelo segue valendo; olhar de novo no próximo lote."
    return "estável", "Nenhuma ação: seguir pontuando", "A carteira e as notas estão como no treino."
