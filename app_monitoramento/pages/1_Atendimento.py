"""Página 1 — Atendimento: o modelo na hora da ligação.

Receptivo: o cliente ligou. A operadora busca pelo código e vê o risco, o porquê, o relato e a escada de ofertas.
Ativo: a operadora liga. A lista de contatos sai da carteira pontuada (inferência), separada pela conversa a ter
(retenção, recuperação, fidelização) e pela receptividade do último relato.
Novo cliente: a operadora monta o pacote pedido e o app compara variações e recomenda a de menor risco.
As ofertas respeitam o plano de marketing (página Plano de marketing).
O cálculo é o do modelo oficial (notebook 06), pelo motor conferido no notebook 10.
"""

import pandas as pd
import streamlit as st

from config.theme import CINZA, COR, DESTAQUE, TEXTO_2, explicar, kpi, legenda, secao_titulo, virg
from motor.modelo import ACOES, NOMES_CONTRATO, NOMES_INTERNET, NOMES_PAGAMENTO, novo_cliente
from utils import catalogo, componentes, frequencias, jornada
from utils.dados import carregar_clientes, carregar_ganho, carregar_motor, carregar_relatos
from utils.pagina import abrir_pagina

abrir_pagina("Atendimento", "Receptivo ou ativo: o risco, o porquê, o relato e o que oferecer", imagem="ilustracao_atendimento.png",
             com_lote=False, carregar=False)
try:
    motor = carregar_motor()
    clientes = carregar_clientes()
    relatos = carregar_relatos()
    ganho = carregar_ganho()
except FileNotFoundError as erro:
    st.error(f"Sem o motor de atendimento: {erro}")
    st.stop()

TAXA_DECIL = dict(zip(ganho["decil"].astype(int), ganho["taxa_churn"].astype(float)))
clientes = clientes.merge(relatos, on="customerID", how="left")
if relatos.empty:
    clientes["abordagem"] = clientes["Churn_Previsto"].map({1: "Retenção", 0: "Fidelização"})
    clientes["receptividade"] = "Média"
clientes[["relato", "tom", "motivos_citados"]] = clientes[["relato", "tom", "motivos_citados"]].fillna("")
clientes["decidiu_sair"] = pd.to_numeric(clientes["decidiu_sair"], errors="coerce").fillna(0).astype(int)
jornada.painel_lateral()
if "comemorar" in st.session_state:                          # celebração do registro anterior (depois do rerun)
    jornada.comemorar(*st.session_state.pop("comemorar"))

COR_FAIXA = {"Alto": DESTAQUE, "Médio": "#E0A100", "Baixo": "#3A7D44"}
PAGAMENTOS = ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"]
CONTRATOS = ["Month-to-month", "One year", "Two year"]
ROTULO_CONTRATO = {"Month-to-month": "Mensal", "One year": "Anual", "Two year": "Dois anos"}
ROTULO_INTERNET = {"Fiber optic": "Fibra", "DSL": "DSL", "No": "Sem internet"}
ROTULO_PAGAMENTO = {"Electronic check": "Cheque eletrônico", "Mailed check": "Boleto pelo correio",
                    "Bank transfer (automatic)": "Débito automático", "Credit card (automatic)": "Cartão automático"}


def caixa_oferta(numero: int, titulo: str, oferta: str, antes: float, depois: float, falas: list, destaque: bool):
    cor = DESTAQUE if destaque else COR
    fala = "".join(f"<li>{f}</li>" for f in falas)
    st.markdown(f"""
<div style="background:#fff;border:1px solid #E5E7EB;border-top:5px solid {cor};border-radius:10px;padding:0.9rem 1.1rem;min-height:250px;">
  <p style="font-size:13px;font-weight:700;color:{cor};text-transform:uppercase;letter-spacing:0.06em;margin:0;">{numero}. {titulo}</p>
  <p style="font-size:1.05rem;font-weight:700;margin:4px 0 2px;">{oferta}</p>
  <p style="font-size:13px;color:{TEXTO_2};margin:0 0 6px;">nota {virg(antes, 2)} → <b style="color:#1A1A1A;">{virg(depois, 2)}</b>
     · decil D{motor.decil(antes)} → D{motor.decil(depois)}{' · sai da zona de risco' if depois < motor.limiar <= antes else ''}</p>
  <ul style="font-size:13.5px;margin:0;padding-left:1.1rem;line-height:1.5;">{fala}</ul>
</div>""", unsafe_allow_html=True)


def kpis_risco(p: float, mensalidade: float, extra_rotulo: str, extra_valor: str, extra_nota: str):
    dec = motor.decil(p)
    faixa = motor.faixa(dec)
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        kpi("Risco", faixa, f"decil D{dec}: no teste, {frequencias.em_10(TAXA_DECIL.get(dec, 0))} clientes desse grupo saíram",
            cor_valor=COR_FAIXA[faixa])
    with c2:
        kpi("Nota do modelo", virg(p, 2), f"limiar {virg(motor.limiar, 2)} · é nota para ordenar, não chance exata")
    with c3:
        kpi("Mensalidade", f"R$ {virg(mensalidade, 2)}", f"R$ {virg(12 * mensalidade, 0)} por ano em jogo")
    with c4:
        kpi(extra_rotulo, extra_valor, extra_nota)



COR_RECEP = {"Alta": "#3A7D44", "Média": "#B07A00", "Baixa": DESTAQUE}
COR_ABORD = {"Retenção": DESTAQUE, "Recuperação": "#8A3B3B", "Fidelização": COR}
ROTEIRO = {
    "Retenção": ("Retenção: o cliente está em risco, mas não disse que vai sair",
                 "Abra pelo relacionamento e confirme se o relato ainda vale. Use o primeiro motivo do modelo como argumento e "
                 "apresente a oferta principal; se ele recusar, desça a escada."),
    "Recuperação": ("Recuperação: o cliente já disse que decidiu sair",
                    "Reconheça a decisão e pergunte se ainda há espaço para conversar. Vá direto à oferta que responde ao "
                    "motivo que ele citou. Se ele recusar, registre e não insista: a reconquista pode vir numa campanha futura."),
    "Fidelização": ("Fidelização: risco baixo e nenhuma queixa",
                    "Ligação de relacionamento: agradeça, pergunte como está o serviço e ofereça só o que ele pedir. "
                    "Não use desconto de retenção com quem não está em risco."),
}


def chip(texto: str, cor: str) -> str:
    return (f'<span style="display:inline-block;border:1px solid {cor};color:{cor};background:#fff;font-size:12.5px;'
            f'font-weight:600;padding:2px 9px;border-radius:12px;margin:0 6px 4px 0;">{texto}</span>')


def bloco_relato(cliente: dict):
    """O último relato do cliente, com a leitura dele e o roteiro de abertura da ligação."""
    abord = cliente.get("abordagem") or "Retenção"
    titulo, roteiro = ROTEIRO[abord]
    motivos_c = [m for m in str(cliente.get("motivos_citados") or "").split("; ") if m]
    chips = chip(abord, COR_ABORD[abord]) + chip(f"Receptividade {str(cliente.get('receptividade') or 'Média').lower()}",
                                                 COR_RECEP.get(cliente.get("receptividade"), TEXTO_2))
    if cliente.get("tom"):
        chips += chip(f"Tom {str(cliente['tom']).lower()}", TEXTO_2)
    chips += "".join(chip(f"Cita: {m.lower()}", TEXTO_2) for m in motivos_c)
    relato = str(cliente.get("relato") or "").replace("$", "R$ ")
    secao_titulo("O QUE O CLIENTE CONTOU", titulo, "Último relato registrado. Confirme na ligação se ainda vale.")
    st.markdown(f"""
<div style="background:#fff;border:1px solid #E5E7EB;border-left:5px solid {COR_ABORD[abord]};border-radius:10px;padding:0.9rem 1.1rem;">
  <div style="margin-bottom:6px;">{chips}</div>
  <p style="font-size:14px;color:#1A1A1A;line-height:1.55;margin:0 0 10px;font-style:italic;">{relato or 'Sem relato registrado.'}</p>
  <p style="font-size:14px;color:#1A1A1A;margin:0;"><b>Como abrir a conversa:</b> {roteiro}</p>
</div>""", unsafe_allow_html=True)
    explicar("""- **Abordagem:** a conversa a ter. **Retenção** = o modelo prevê saída e o cliente não disse que vai sair.
**Recuperação** = o relato já diz que ele decidiu sair (a mesma regra do notebook 04, que acerta 98,9% no histórico).
**Fidelização** = risco baixo.
- **Receptividade:** a chance de ele ouvir uma oferta, pelo tom do relato: alta (positivo), média (misto ou neutro),
baixa (negativo ou saída já decidida). É uma aproximação até existir o histórico de contatos.
- **Cita:** os motivos de queixa que aparecem no relato (preço, conexão, atendimento, contrato, forma de pagamento, concorrência).

**O relato não entra na nota do modelo:** ele foi escrito depois da decisão do cliente (vazamento, decisão D9). Aqui ele só
escolhe a conversa. Os valores do relato estão em reais (o texto original usa o símbolo $).""", "Como ler o relato")


def bloco_historico(cid: str):
    secao_titulo("HISTÓRICO DE CONTATOS", "O que já aconteceu com este cliente",
                 "Cada atendimento registrado aqui entra no histórico. É ele que vai mostrar quem ligou várias vezes reclamando.")
    h = jornada.historico(cid)
    if h.empty:
        st.markdown(f"<p style='font-size:14px;color:{TEXTO_2};margin:0;'>Nenhum contato registrado com este cliente. A base da "
                    "Terra Signal ainda não tem o histórico de ligações e de suporte: o registro no fim desta página começa "
                    "esse histórico.</p>", unsafe_allow_html=True)
    else:
        st.dataframe(h.rename(columns={"data": "Data", "hora": "Hora", "tipo": "Tipo", "abordagem": "Abordagem",
                                       "resultado": "Resultado", "oferta": "Oferta aceita", "anotacao": "Anotação"}),
                     hide_index=True, use_container_width=True)


def painel_cliente(cid: str, ordem: list, modo: str):
    """Tudo o que a operadora precisa de um cliente da carteira: risco, relato, histórico, motivos, ofertas e registro."""
    feitos = jornada.registrados()
    cliente = clientes.set_index("customerID").loc[cid].to_dict()
    cliente["customerID"] = cid
    p0 = motor.prob1(cliente)
    todas = motor.ofertas(cliente)
    of = catalogo.filtrar(todas, cliente.get("segmento"))
    principal = of.sort_values("nota_depois").iloc[0]["oferta"] if not of.empty else "nenhuma liberada"
    frequencias.resumo_cliente(cliente, TAXA_DECIL.get(motor.decil(p0), 0.0), motor.decil(p0),
                               cliente.get("abordagem") or "Retenção", principal)
    explicar("""**Clientes como ele:** a taxa real de saída do grupo de risco (decil) do cliente, medida nos clientes de teste, que o
modelo não viu. É mais honesta que a nota do modelo, que é inflada pelo balanceamento (no D1, a nota média é 0,89 e saem 76%).

**As quatro variáveis-chave:** as que mais separam quem sai de quem fica e que a empresa consegue mudar (exceto o tempo
de casa). O \"X em cada 10\" é a taxa de saída dos clientes do histórico com a mesma situação (5.634 clientes):
contrato mensal, 4 em cada 10; até 6 meses de casa, 5 em cada 10; fibra sem suporte, 5 em cada 10; cheque eletrônico,
quase 5 em cada 10. Ao lado, a ação que responde a cada uma.""", "Como ler o resumo")

    kpis_risco(p0, cliente["MonthlyCharges"], "Segmento", str(cliente["segmento"]),
               f"{cliente['nome_segmento']} · {cliente['quadrante']}")
    explicar("""- **Risco:** Alto (decis D1 e D2), Médio (D3 a D5) ou Baixo (D6 a D10). O decil é a posição do cliente na carteira: D1 são os 10% de maior risco.
- **Nota do modelo:** a probabilidade da logística, de 0 a 1. Acima do limiar (0,50), o cliente entra na fila. Serve para ordenar: no D1, a nota média é 0,89, mas saem 76%.
- **Mensalidade:** o valor do último mês; por ano, é o que está em jogo se ele sair.
- **Segmento e quadrante:** o tipo de cliente (notebook 07) e a combinação de risco e valor (salvar já, ação barata, fidelizar, manter).""", "O que significam estes números")

    st.markdown(
        f"<p style='font-size:14px;color:{TEXTO_2};margin:0.8rem 0 0;'>Cliente há <b>{int(cliente['tenure'])} "
        f"{'mês' if int(cliente['tenure']) == 1 else 'meses'}</b> · "
        f"contrato <b>{NOMES_CONTRATO[cliente['Contract']]}</b> · <b>{NOMES_INTERNET[cliente['InternetService']]}</b> · paga por "
        f"<b>{NOMES_PAGAMENTO[cliente['PaymentMethod']]}</b> · suporte técnico: <b>{'sim' if cliente['TechSupport'] == 'Yes' else 'não'}</b> · "
        f"segurança online: <b>{'sim' if cliente['OnlineSecurity'] == 'Yes' else 'não'}</b></p>", unsafe_allow_html=True)

    bloco_relato(cliente)
    bloco_historico(cid)

    mot = motor.motivos(cliente)
    topo = (f"O que mais pesa: {mot.index[0].lower()} ({mot['descricao'].iloc[0]})" if mot["efeito"].iloc[0] >= 0.05
            else "Nada empurra o risco para cima")
    secao_titulo("POR QUE ELE ESTÁ EM RISCO", topo, "Cada linha é um tema do modelo, com os dados do próprio cliente.")
    componentes.motivos(mot)
    legenda([(DESTAQUE, "aumenta o risco deste cliente", "barra"), (CINZA, "protege", "barra"),
             ("#9CA3AF", "cliente médio do treino (zero)", "linha")])
    explicar("""Na regressão logística, a nota é a soma de pedaços: cada variável soma **coeficiente × valor padronizado**. Juntando as
variáveis do mesmo tema (tempo de casa, contrato, pagamento, suporte, pacote, perfil), sai quanto cada tema empurra a nota
**deste** cliente para cima ou para baixo, em relação a um cliente médio.

- **Pesa muito / pesa / pesa pouco:** quanto o tema aumenta o risco.
- **Neutro:** o cliente está perto da média nesse tema.
- **Protege:** o tema puxa a nota para baixo (por exemplo, contrato de dois anos).

Use os primeiros temas para escolher o argumento da ligação.""", "Como ler os motivos")

    secao_titulo("O QUE OFERECER", "A escada de ofertas",
                 "Comece pela primeira; se o cliente recusar, desça para a próxima. Só aparecem as ofertas liberadas no plano de marketing.")
    escolhidos = []
    if todas.empty:
        st.info("Cliente sem ação de retenção disponível: já tem contrato de dois anos, pagamento automático e proteção.")
    elif of.empty:
        st.info("Nenhuma oferta liberada no plano de marketing para este cliente. Veja a página Plano de marketing.")
    else:
        tem_contrato = of["acoes"].apply(lambda a: any(x.startswith("contrato") for x in a))
        tem_2anos = of["acoes"].apply(lambda a: "contrato_2anos" in a)
        degraus = [("Oferta principal", of), ("Se recusar fidelidade de dois anos", of[~tem_2anos]),
                   ("Se recusar mudar o contrato", of[~tem_contrato])]
        vistos = set()
        for titulo, sub in degraus:
            if sub.empty or sub.iloc[0]["oferta"] in vistos:
                continue
            vistos.add(sub.iloc[0]["oferta"])
            escolhidos.append((titulo, sub.iloc[0]))
        for num, ((titulo, linha), col) in enumerate(zip(escolhidos, st.columns(3, gap="medium")), start=1):
            with col:
                caixa_oferta(num, titulo, linha["oferta"], p0, linha["nota_depois"],
                             [catalogo.fala(a) for a in linha["acoes"]], destaque=num == 1)
        explicar("""**Comece pelo cartão 1 e desça se o cliente recusar.**

1. **Oferta principal:** a combinação de até duas ações que mais baixa a nota.
2. **Se recusar fidelidade de dois anos:** a melhor sem o contrato de dois anos.
3. **Se recusar mudar o contrato:** a melhor mexendo só em pagamento, suporte ou segurança.

**Nota antes → depois:** quanto a nota cai se ele aceitar, pelo modelo. **Decil antes → depois:** a nova posição na carteira.
Suporte e segurança entram como cortesia (mensalidade igual). As falas e as ofertas liberadas vêm do plano de marketing.

A queda da nota é o que o modelo associa à mudança, não a garantia de que o cliente fica.""", "Como usar a escada")
        st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)
        if p0 < motor.limiar:
            st.caption("Este cliente está abaixo do limiar: as ofertas servem para fidelizar, não para uma ação de retenção.")
        elif of.iloc[0]["nota_depois"] >= motor.limiar:
            causa = (f"o maior motivo é o tempo de casa ({mot.loc['Tempo de casa', 'descricao']}), que nenhuma oferta muda. "
                     "Além da oferta, combine o acompanhamento dos primeiros meses: contato de boas-vindas, "
                     "checagem da instalação e um ponto de contato fixo."
                     if mot.index[0] == "Tempo de casa" else
                     "o risco dele vem de fatores que as ofertas não mudam. Priorize um contato pessoal para entender o motivo.")
            st.warning(f"Mesmo com a melhor oferta, o cliente continua acima do limiar: {causa}")

    # ── Simulador ─────────────────────────────────────────────────────────────
    secao_titulo("SIMULADOR", "E se ele aceitar?",
                 "Marque o que o cliente aceitou: a nota é recalculada pelo modelo oficial na hora. "
                 "Suporte e segurança entram como cortesia (mensalidade igual).")
    s1, s2, s3, s4 = st.columns([1.6, 1, 1, 1])
    with s1:
        contrato_atual = cliente["Contract"]
        opcoes_contrato = CONTRATOS[CONTRATOS.index(contrato_atual):]
        novo_contrato = st.radio("Contrato", opcoes_contrato, format_func=ROTULO_CONTRATO.get, key=f"ct_{cid}",
                                 horizontal=True)
    with s2:
        trocar_pag = st.toggle("Débito automático", key=f"pg_{cid}",
                               disabled=not ACOES["debito_automatico"]["vale"](cliente))
    with s3:
        sup = st.toggle("Suporte técnico", key=f"sp_{cid}", disabled=not ACOES["suporte"]["vale"](cliente))
    with s4:
        segu = st.toggle("Segurança online", key=f"sg_{cid}", disabled=not ACOES["seguranca"]["vale"](cliente))
    acoes = ([{"One year": "contrato_anual", "Two year": "contrato_2anos"}[novo_contrato]] if novo_contrato != contrato_atual else [])
    acoes += [a for a, ligado in [("debito_automatico", trocar_pag), ("suporte", sup), ("seguranca", segu)]
              if ligado and ACOES[a]["vale"](cliente)]
    p1 = motor.prob1(motor.aplicar(cliente, acoes))
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        kpi("Nota hoje", virg(p0, 2), f"decil D{motor.decil(p0)} · risco {motor.faixa(motor.decil(p0)).lower()}")
    with c2:
        kpi("Nota com a oferta", virg(p1, 2), f"decil D{motor.decil(p1)} · risco {motor.faixa(motor.decil(p1)).lower()}",
            cor_valor=COR if p1 < motor.limiar else DESTAQUE)
    with c3:
        kpi("Queda da nota", virg(p0 - p1, 2), "acima do limiar" if p1 >= motor.limiar else "abaixo do limiar: sai da fila",
            cor_valor=COR if p0 - p1 > 0 else TEXTO_2)
    componentes.regua(p0, p1 if acoes else None, motor.limiar)
    legenda([("#4B5563", "nota hoje", "ponto"), (COR, "com a oferta, abaixo do limiar", "ponto"),
             (DESTAQUE, "com a oferta, ainda acima", "ponto"), ("#9CA3AF", "limiar (0,50)", "tracejado"),
             ("#EEF4F6", "fora da fila", "zona"), ("#FBEFE3", "na fila de retenção", "zona")])
    st.caption("A queda da nota é o que o modelo associa à mudança, não a garantia de que o cliente fica. "
               "A taxa real de aceite e de permanência se mede com um teste em parte da fila.")

    # ── Registro do atendimento (roteiro, missões e XP) ──────────────────────
    secao_titulo("REGISTRAR O ATENDIMENTO", "Como terminou a ligação?",
                 "Marque o roteiro, escolha o resultado e registre. Cada registro vale XP, conta para as missões do dia e "
                 "entra no histórico de contatos do cliente.")
    explicar(f"""**Por que registrar:** cada registro diz se a oferta funcionou e forma o histórico de contatos do cliente. Com esses
dados, a empresa mede o resultado real das ofertas e o recall do modelo, e treina o próximo passo (o modelo de uplift:
qual oferta funciona para qual cliente).

**Roteiro da ligação:** os 4 passos que fazem uma boa conversa. Com os 4 marcados, +5 XP.

**Como o XP é contado:** 10 por registrar; +5 se começou pela oferta principal; +10 se o cliente é do D1; +10 se aceitou;
+5 pelo roteiro completo; +{jornada.XP_MISSAO} por missão do dia cumprida. O XP premia registrar e seguir o roteiro, não
pressionar o cliente.

**Na barra lateral:** a meta do dia, as missões, o nível, a sequência na escada, o impacto em reais e as conquistas.""",
             "Como funciona o registro e o XP")
    if cid in feitos:
        st.success("Atendimento deste cliente já registrado (veja o histórico acima). Escolha o próximo contato.")
        return
    dec0 = motor.decil(p0)
    r0, r1, r2, r3 = st.columns([1.2, 1.2, 1.2, 0.9], gap="large")
    with r0:
        st.markdown("**Roteiro da ligação**")
        marcados = [st.checkbox(passo, value=False, key=f"passo{i}_{cid}") for i, passo in enumerate(jornada.PASSOS)]
        seguiu = marcados[2]
        passos = sum(marcados)
    with r1:
        resultado = st.radio("Resultado", list(jornada.RESULTADOS), format_func=jornada.RESULTADOS.get, key=f"res_{cid}")
    with r2:
        oferta_aceita, acoes_aceitas = "", ()
        if resultado == "principal" and escolhidos:
            oferta_aceita, acoes_aceitas = escolhidos[0][1]["oferta"], escolhidos[0][1]["acoes"]
            st.markdown(f"**Oferta aceita:** {oferta_aceita}")
        elif resultado == "alternativa" and len(escolhidos) > 1:
            alt = st.selectbox("Qual alternativa?", [l["oferta"] for _, l in escolhidos[1:]], key=f"alt_{cid}")
            linha_alt = next(l for _, l in escolhidos[1:] if l["oferta"] == alt)
            oferta_aceita, acoes_aceitas = alt, linha_alt["acoes"]
        anotacao = st.text_input("Anotação da ligação", key=f"nota_{cid}",
                                 placeholder="Ex.: reclamou de quedas na conexão; pediu retorno à tarde")
    with r3:
        xp_prev = jornada.xp_do_registro(dec0, resultado, seguiu, passos)
        st.markdown(f"<p style='font-size:13px;color:{TEXTO_2};margin:0;'>Este registro vale</p>"
                    f"<p style='font-size:2rem;font-weight:700;color:{DESTAQUE};margin:0;'>+{xp_prev} XP</p>"
                    f"<p style='font-size:13px;color:{TEXTO_2};margin:0 0 8px;'>mais {jornada.XP_MISSAO} por missão cumprida</p>",
                    unsafe_allow_html=True)
        if st.button("Registrar e ir para o próximo", type="primary", use_container_width=True, key=f"reg_{cid}"):
            antes = jornada.resumo()["n"]
            xp, novas = jornada.registrar(cliente, dec0, resultado, seguiu, oferta_aceita, tuple(acoes_aceitas),
                                          abordagem=cliente.get("abordagem") or "", modo=modo, passos=passos, nota=anotacao)
            meta = jornada.estado()["meta"]
            st.session_state["comemorar"] = (xp, novas, antes < meta <= antes + 1)
            feitos_agora = jornada.registrados()
            seguinte = next((c for c in ordem[ordem.index(cid) + 1:] + ordem if c not in feitos_agora), None) if cid in ordem else None
            if seguinte:
                st.session_state[f"proximo_{modo}"] = seguinte
            st.rerun()


def rotulo_cliente(r) -> str:
    return (f"{r.customerID}  ·  {r.segmento} {r.nome_segmento}  ·  nota {virg(r.Probabilidade_Churn, 2)}"
            + ("  ·  registrado" if r.customerID in jornada.registrados() else ""))


def escolher(base: pd.DataFrame, chave: str, rotulo_campo: str, ajuda: str):
    """Selectbox de clientes que respeita o 'próximo' sugerido depois de um registro."""
    rotulo = {r.customerID: rotulo_cliente(r) for r in base.itertuples()}
    proximo = st.session_state.pop(f"proximo_{chave}", None)
    if proximo in rotulo:
        st.session_state[f"sel_{chave}"] = proximo
    elif st.session_state.get(f"sel_{chave}") not in rotulo:
        st.session_state.pop(f"sel_{chave}", None)
    if not rotulo:
        return None, []
    cid = st.selectbox(rotulo_campo, list(rotulo), format_func=rotulo.get, key=f"sel_{chave}", help=ajuda)
    return cid, list(rotulo)


MODOS = {"Receptivo": "Receptivo: o cliente ligou", "Ativo": "Ativo: eu ligo para a minha lista",
         "Novo cliente": "Novo cliente: quer contratar"}
if st.session_state.get("modo") not in MODOS:
    st.session_state["modo"] = "Receptivo"
modo = st.radio("Tipo de atendimento", list(MODOS), format_func=MODOS.get, horizontal=True, key="modo",
                label_visibility="collapsed")

# ═════════════════════════════════════════════════════════════════════════════
# RECEPTIVO: o cliente ligou
# ═════════════════════════════════════════════════════════════════════════════
if modo == "Receptivo":
    col_busca, col_filtro = st.columns([3, 1])
    with col_filtro:
        so_fila = st.toggle("Só a fila de retenção", value=False, help="Clientes previstos como Yes pelo modelo")
    base = clientes[clientes["Churn_Previsto"] == 1] if so_fila else clientes
    with col_busca:
        cid, ordem = escolher(base, "Receptivo", "Quem está na linha? (digite o código do cliente)",
                              "Toda a carteira pontuada, do maior para o menor risco")
    if cid:
        painel_cliente(cid, ordem, "Receptivo")

# ═════════════════════════════════════════════════════════════════════════════
# ATIVO: a lista de quem ligar
# ═════════════════════════════════════════════════════════════════════════════
if modo == "Ativo":
    contagem = clientes["abordagem"].value_counts()
    secao_titulo("MINHA LISTA DE LIGAÇÕES", "Quem ligar hoje, e com que conversa",
                 "A carteira pontuada pelo modelo, separada pela conversa a ter e ordenada pela receptividade e pela nota.")
    k1, k2, k3 = st.columns(3, gap="medium")
    with k1:
        kpi("Retenção", virg(int(contagem.get("Retenção", 0)), 0), "previstos para sair, sem saída declarada",
            cor_valor=COR_ABORD["Retenção"])
    with k2:
        kpi("Recuperação", virg(int(contagem.get("Recuperação", 0)), 0), "o relato já diz que decidiram sair",
            cor_valor=COR_ABORD["Recuperação"])
    with k3:
        kpi("Fidelização", virg(int(contagem.get("Fidelização", 0)), 0), "risco baixo, nenhuma queixa",
            cor_valor=COR_ABORD["Fidelização"])
    explicar("""- **Retenção:** o modelo prevê saída (nota acima do limiar) e o relato não diz que o cliente já decidiu. É onde a
oferta mais rende.
- **Recuperação:** o relato diz que o cliente decidiu sair. A conversa é de reconquista, com a oferta que responde ao motivo citado.
- **Fidelização:** risco baixo; ligação de relacionamento, sem desconto de retenção.

A lista vem da **carteira pontuada (inferência, 1.409 clientes)**, e não do histórico: no histórico, o desfecho já é conhecido.
Dentro de cada conversa, a ordem é **receptividade** (alta primeiro) e depois **nota do modelo** (maior primeiro).""",
             "Como a lista é montada")
    f1, f2, f3 = st.columns([1.4, 1.2, 1.2], gap="medium")
    with f1:
        abord = st.radio("Conversa", ["Retenção", "Recuperação", "Fidelização"], horizontal=True, key="ativo_abord")
    with f2:
        recep = st.multiselect("Receptividade", ["Alta", "Média", "Baixa"], default=["Alta", "Média", "Baixa"], key="ativo_recep")
    with f3:
        segs = st.multiselect("Segmento", sorted(clientes["segmento"].dropna().unique()), key="ativo_seg",
                              format_func=lambda s: f"{s} {clientes.loc[clientes['segmento'] == s, 'nome_segmento'].iloc[0]}")
    lista = clientes[(clientes["abordagem"] == abord) & clientes["receptividade"].isin(recep or ["Alta", "Média", "Baixa"])]
    if segs:
        lista = lista[lista["segmento"].isin(segs)]
    ordem_recep = {"Alta": 0, "Média": 1, "Baixa": 2}
    lista = lista.assign(_r=lista["receptividade"].map(ordem_recep)).sort_values(["_r", "Probabilidade_Churn"],
                                                                                 ascending=[True, False]).drop(columns="_r")
    feitos = jornada.registrados()
    pendentes = lista[~lista["customerID"].isin(feitos)]
    st.markdown(f"<p style='font-size:14px;color:#1A1A1A;margin:0.4rem 0;'><b>{virg(len(pendentes), 0)}</b> clientes a ligar "
                f"nesta lista · <b>{len(lista) - len(pendentes)}</b> já registrados hoje</p>", unsafe_allow_html=True)
    vis = lista.head(12).assign(
        Status=lambda d: d["customerID"].isin(feitos).map({True: "Registrado", False: "A ligar"}),
        Nota=lambda d: d["Probabilidade_Churn"].round(2),
        Cliente=lambda d: d["customerID"],
        Perfil=lambda d: d["segmento"] + " · " + d["Contract"].map(ROTULO_CONTRATO) + " · " + d["InternetService"].map(ROTULO_INTERNET),
        Receptividade=lambda d: d["receptividade"],
        Cita=lambda d: d["motivos_citados"].replace("", "—"),
        Oferta=lambda d: d["oferta_principal"].fillna("—"),
    )[["Status", "Cliente", "Perfil", "Nota", "Receptividade", "Cita", "Oferta"]]
    st.dataframe(vis, hide_index=True, use_container_width=True,
                 column_config={"Nota": st.column_config.ProgressColumn("Nota", min_value=0, max_value=1, format="%.2f")})
    st.caption("Os 12 primeiros da lista. Escolha abaixo quem ligar; depois de registrar, o app abre o próximo.")
    base_ativo = pd.concat([pendentes, lista[lista["customerID"].isin(feitos)]])
    cid, ordem = escolher(base_ativo, "Ativo", "Próximo contato", "A lista acima, sem os já registrados primeiro")
    if cid:
        painel_cliente(cid, ordem, "Ativo")
    else:
        st.info("Nenhum cliente nesta lista com os filtros escolhidos.")

# ═════════════════════════════════════════════════════════════════════════════
# NOVO CLIENTE
# ═════════════════════════════════════════════════════════════════════════════
if modo == "Novo cliente":
    secao_titulo("QUEM ESTÁ NA LINHA", "Monte o pacote que o cliente pediu",
                 "O app estima a mensalidade pela tabela de preço da Terra Signal e compara variações do mesmo pacote.")
    f1, f2, f3 = st.columns([1, 1.3, 1.1], gap="large")
    with f1:
        st.markdown("**Perfil**")
        idoso = st.toggle("65 anos ou mais")
        parceiro = st.toggle("Tem parceiro(a)")
        dependentes = st.toggle("Tem dependentes")
    with f2:
        st.markdown("**Pacote pedido**")
        internet = st.radio("Internet", ["Fiber optic", "DSL", "No"], format_func=ROTULO_INTERNET.get, horizontal=True)
        telefone = st.toggle("Telefone fixo", value=True)
        linhas = st.toggle("Mais de uma linha", disabled=not telefone)
        servicos = {}
        if internet != "No":
            cs1, cs2 = st.columns(2)
            with cs1:
                servicos["StreamingTV"] = st.checkbox("Streaming de TV")
                servicos["StreamingMovies"] = st.checkbox("Streaming de filmes")
                servicos["OnlineBackup"] = st.checkbox("Backup online")
            with cs2:
                servicos["DeviceProtection"] = st.checkbox("Proteção de aparelho")
                servicos["TechSupport"] = st.checkbox("Suporte técnico")
                servicos["OnlineSecurity"] = st.checkbox("Segurança online")
    with f3:
        st.markdown("**Condições pedidas**")
        contrato = st.selectbox("Contrato", CONTRATOS, format_func=ROTULO_CONTRATO.get)
        pagamento = st.selectbox("Forma de pagamento", PAGAMENTOS, format_func=ROTULO_PAGAMENTO.get)
        fatura = st.toggle("Fatura digital", value=True)

    if not telefone and internet == "No":
        st.warning("Escolha pelo menos telefone ou internet.")
        st.stop()

    perfil = {"idoso": idoso, "parceiro": parceiro, "dependentes": dependentes, "renda": None}
    pedido = {"internet": internet, "telefone": telefone, "linhas_multiplas": linhas and telefone, "contrato": contrato,
              "pagamento": pagamento, "fatura_digital": fatura, **servicos}

    # variações do pacote: contrato × pagamento × suporte e segurança
    linhas_opc = []
    pag_auto = pagamento if "automatic" in pagamento else "Bank transfer (automatic)"
    for ct in CONTRATOS:
        for pg in dict.fromkeys([pagamento, pag_auto]):
            for prot in ([False, True] if internet != "No" else [False]):
                pac = dict(pedido, contrato=ct, pagamento=pg)
                if prot:
                    pac.update(TechSupport=True, OnlineSecurity=True)
                c = novo_cliente(perfil, pac, motor)
                linhas_opc.append({"contrato": ct, "pagamento": pg, "protecao": prot, "mensalidade": c["MonthlyCharges"],
                                   "nota": motor.prob1(c), "pac": pac})
    opc = pd.DataFrame(linhas_opc)
    opc["chave"] = opc["contrato"] + opc["pagamento"] + opc["mensalidade"].round(2).astype(str)
    opc = opc.drop_duplicates("chave").sort_values("nota").reset_index(drop=True)
    preco_pedido = novo_cliente(perfil, pedido, motor)["MonthlyCharges"]
    opc["pedido"] = (opc["contrato"] == contrato) & (opc["pagamento"] == pagamento) & ((opc["mensalidade"] - preco_pedido).abs() < 0.01)
    opc["recomendado"] = False
    opc.loc[0, "recomendado"] = True
    extra = not (servicos.get("TechSupport") and servicos.get("OnlineSecurity"))
    opc["rotulo"] = [f"{ROTULO_CONTRATO[r.contrato]} · {ROTULO_PAGAMENTO[r.pagamento].lower()}"
                     + (" · + suporte e segurança" if r.protecao and extra else "") for r in opc.itertuples()]
    mesmo_preco = opc[(opc["mensalidade"] - preco_pedido).abs() < 0.01].iloc[0]
    ped = opc[opc["pedido"]].iloc[0]
    rec = opc.iloc[0]

    secao_titulo("O QUE OFERECER", f"Ofereça: {rec['rotulo']}",
                 f"Entre as variações do que o cliente pediu, é a de menor nota de risco no primeiro mês "
                 f"({virg(ped['nota'], 2)} → {virg(rec['nota'], 2)}).")
    def dif(v):
        d = v - ped["mensalidade"]
        return "mesmo preço do pedido" if abs(d) < 0.01 else f"{'+' if d > 0 else '−'}R$ {virg(abs(d), 2)} por mês"
    k1, k2, k3 = st.columns(3, gap="medium")
    with k1:
        kpi("Pacote pedido", virg(ped["nota"], 2), f"{ped['rotulo']} · R$ {virg(ped['mensalidade'], 2)}",
            cor_valor="#4B5563")
    with k2:
        kpi("Recomendado", virg(rec["nota"], 2), f"{rec['rotulo']} · R$ {virg(rec['mensalidade'], 2)} ({dif(rec['mensalidade'])})",
            cor_valor=DESTAQUE)
    with k3:
        kpi("Sem mudar o preço", virg(mesmo_preco["nota"], 2),
            f"{mesmo_preco['rotulo']} · R$ {virg(mesmo_preco['mensalidade'], 2)}", cor_valor=COR)
    st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)

    componentes.pacotes(opc, motor.limiar)
    legenda([(DESTAQUE, "recomendado (menor nota)", "barra"), ("#4B5563", "pedido pelo cliente", "barra"),
             ("#D7DCE0", "outras variações", "barra"), ("#4B5563", "limiar", "tracejado")])
    explicar("""**Cada linha é uma variação do pacote pedido:** os três contratos, com e sem débito automático, com e sem suporte e
segurança. A barra é a nota de risco no **primeiro mês**; a mensalidade vem da tabela de preço.

Todo cliente novo tem nota alta, porque está no primeiro mês (o tempo de casa é o que mais pesa). A comparação serve para
**ordenar** os pacotes, não para dizer que o cliente vai sair. O contrato de dois anos para quem está começando é raro no
histórico: a nota desses pacotes é uma extrapolação.""", "Como ler a comparação")
    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    a2, a3 = st.columns([1.6, 1], gap="large")
    with a2:
        argumentos = []
        if rec["contrato"] != contrato:
            argumentos.append(f"<b>Contrato {ROTULO_CONTRATO[rec['contrato']].lower()}:</b> ofereça desconto nos primeiros meses em troca da fidelidade.")
        if rec["pagamento"] != pagamento:
            argumentos.append("<b>Débito automático:</b> desconto na fatura e nada de boleto ou cheque para lembrar.")
        if rec["protecao"] and not (servicos.get("TechSupport") and servicos.get("OnlineSecurity")):
            argumentos.append("<b>Suporte e segurança:</b> R$ 10 a mais por mês, ou cortesia nos primeiros meses.")
        if not argumentos:
            argumentos.append("O pacote pedido já é o de menor risco: feche como está.")
        caixa_mesmo = ""
        st.markdown(f"""
<div style="background:#fff;border:1px solid #E5E7EB;border-left:5px solid {DESTAQUE};border-radius:10px;padding:0.9rem 1.1rem;">
  <p style="font-size:13px;font-weight:700;color:{DESTAQUE};text-transform:uppercase;letter-spacing:0.06em;margin:0;">Argumento para a operadora</p>
  <ul style="font-size:13.5px;margin:0.4rem 0 0;padding-left:1.1rem;line-height:1.55;">{''.join(f'<li>{a}</li>' for a in argumentos)}</ul>
  {caixa_mesmo}
</div>""", unsafe_allow_html=True)
        tab = pd.DataFrame({"Tabela de preço": ["Telefone", "Linha extra", "Internet DSL", "Internet fibra", "Cada proteção",
                                                "Cada streaming"],
                            "R$ por mês": [motor.preco["telefone"], motor.preco["linhas_multiplas"], motor.preco["dsl"],
                                           motor.preco["fibra"], motor.preco["TechSupport"], motor.preco["StreamingTV"]]})
        tab["R$ por mês"] = tab["R$ por mês"].map(lambda v: f"R$ {virg(v, 0)}")
    with a3:
        st.dataframe(tab, hide_index=True, use_container_width=True)
        explicar("""A mensalidade é, na prática, a soma de uma tabela fixa: uma regressão linear da mensalidade pelos itens do pacote
explica **99,9%** da variação no histórico (notebook 10). É assim que o app estima o preço de um pacote que ainda não existe.""",
                 "De onde vem a tabela")
    st.caption("Cliente novo: a nota é a do primeiro mês. Quase ninguém começa no contrato de dois anos no histórico, então a nota "
               "desses pacotes é uma extrapolação: serve para ordenar as opções, não como previsão exata.")
