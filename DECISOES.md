# Decisões do projeto: Terra Signal (Grupo 4)

Todas as decisões tomadas na preparação dos dados, com o motivo, a evidência e onde cada uma está aplicada. É a mesma
numeração do **checklist de decisões** que abre cada notebook (D1 a D25; a D26 está no notebook 11).

| Símbolo | Significado |
|---|---|
| ☑ | Decidido pelo grupo (com a data) |
| ◐ | Sugestão da preparação; a seleção final é feita na modelagem (D18) |
| ☐ | Em aberto |

Siglas por extenso: ver o glossário no início dos notebooks 03, 04 e 05.

---

## Resumo

| # | Decisão | Status | Onde está aplicada |
|---|---|---|---|
| D1 | `PhoneService`: padronizar `yes`/`no` para `Yes`/`No` | ☑ 10/11 | 02 |
| D2 | `TotalCharges` nulo: preencher com `MonthlyCharges` × `tenure` | ☑ 10/11 | 02 |
| D3 | `TotalCharges` nulo com `tenure` = 0: vira 0 | ☑ 10/11 | 02 |
| D4 | `tenure` = `unknown`: recuperar por `TotalCharges` ÷ `MonthlyCharges`; mediana no caso sem os dois | ☑ 10/11 | 02 |
| D5 | Criar o indicador `fl_total_charges_ausente` | ☑ 10/11 | 02 |
| D6 | Não criar indicador para `tenure` | ☑ 10/11 | 02 |
| D7 | Manter os 47 + 9 clientes fora de ±20% da regra | ☑ 10/11 | 02 |
| D8 | Trocar as quebras de linha do comentário por espaço | ☑ 10/11 | 02 |
| D9 | Texto do comentário fora do modelo oficial e da ABT; modelo com texto só como contraexemplo | ☑ 10/11 | 03, 04, 05 |
| D10 | Serviços como sim/não (`_bin`), junto com `InternetService` | ◐ | 04, 05 |
| D11 | Fonte única: tabelas `bronze_*` em `workspace.terra_signal` | ☑ 10/11 | 01, 02 |
| D12 | `MonthlyIncome`: sugestão de descartar | ◐ | 03, 04 |
| D13 | `Prediction.csv` com 1.409 linhas, uma por `customerID` | ☑ 10/11 (a confirmar) | Entrega |
| D14 | Formato da gold: ABT com todas as candidatas + dicionário com sugestão + texto separado | ☑ 10/11 | 04 |
| D15 | `gender`, `PhoneService`, `MultipleLines`: sugestão de descartar | ◐ | 03, 04 |
| D16 | `MonthlyCharges` e `TotalCharges`: manter a mensalidade (ou a relativa ao pacote) e descartar o total | ◐ | 04 |
| D17 | O 03 lê das tabelas bronze | ☑ 10/11 | 03 |
| D18 | A preparação entrega a ABT e sugere; a seleção final das variáveis é feita na modelagem | ☑ 10/11 | 04, 05 |
| D19 | Seleção de variáveis: 41 colunas (testes estatísticos com FDR e retirada de duplicatas), conferidas com os métodos da aula (11 variáveis) | ☑ 11/11 | 05 |
| D20 | Segmentação: K-means no comportamento (5 segmentos), sem o churn, cruzado com risco × valor | ◐ 11/11 | 07 |
| D21 | Modelo final: logística Lasso, C = 0,3, classes balanceadas, 41 colunas (vencedora pela regra de consistência; a Ridge ficou a 0,003) | ☑ 11/11 | 06 |
| D22 | Limiar do Sim/Não: 0,5046, o que maximiza o F1 fora da dobra do treino | ☑ 11/11 | 06 |
| D23 | Arquivo da entrega: `prediction_grupo4_<data_hora>.csv`, 1.409 linhas, `customerID` e `prediction` (Yes/No); 571 com Yes (40,5%) | ☑ 11/11 | 08 |
| D24 | Monitoramento: PSI das variáveis e das notas, taxa de Yes, reprodução pelo MLflow e qualidade dos dados, com semáforo e ações no app | ◐ 12/11 | 09 |
| D25 | Motor de atendimento: nota, motivos e escada de ofertas por cliente, pacote para novo cliente e simulador de campanha, conferidos contra o modelo oficial | ◐ 12/11 | 10 |
| D26 | Comentário lido por LLM (`ai_query`): situação relatada, sentimento e motivos, para orientar a conversa; fora do modelo | ◐ 12/11 | 11 |

---

## 1. Fonte e arquitetura

### D11 — Fonte única do grupo ☑
- **Decisão:** todos leem as tabelas `bronze_history` e `bronze_inference` em `workspace.terra_signal`. As tabelas do upload em `workspace.default` são ignoradas, sem apagar.
- **Por quê:** o upload pela interface quebrou os registros nas quebras de linha do comentário (5.773 linhas em vez de 5.634). A bronze tem a contagem certa, e uma fonte só faz os números baterem entre todos.
- **Evidência:** 01, seções 1.2 e 2.
- **Aplicada:** o 02 lê da bronze; o 03 e o 04 também (D17).

### D17 — Fonte do 03 ☑
- **Decisão:** a análise exploratória lê das tabelas bronze.
- **Por quê:** coerência com a D11. É o mesmo dado dos CSVs, então os números não mudam.

### D14 — Formato da gold ☑
- **Decisão:** a camada gold tem:
  - `gold_churn_treino`: 5.634 clientes, 49 candidatas e `Churn`;
  - `gold_churn_inferencia`: 1.409 clientes, mesmas colunas e ordem;
  - `gold_churn_dicionario`: origem, fórmula, IV e sugestão de cada coluna;
  - `gold_churn_texto`: o comentário, separado (D9);
  - `gold_churn_selecao`: a conferência da seleção com os métodos da aula (D19);
  - `gold_churn_split` e `gold_churn_variaveis_modelo`: a separação treino/teste e as 41 colunas do modelo (05).
- **Por quê:** é o que a modelagem usa. Números como número e categorias como texto, para cada modelo codificar do seu jeito. Formato estável evita retrabalho.
- **Aplicada:** 04 (gravação) e 05 (teste de carga com 12 regras).

### D18 — Divisão de papéis ☑
- **Decisão:** a preparação entrega a ABT (*Analytical Base Table*) e **sugere**; a **seleção final** das variáveis é feita no 05 (testes estatísticos) e usada pela modelagem (06).
- **Consequência:** a ABT traz todas as candidatas, inclusive as que sugerimos descartar. As sugestões (◐) ficam registradas no dicionário, com o motivo.

---

## 2. Limpeza dos dados (aplicada no 02)

| # | Problema | Casos (histórico + inferência) | Decisão | Por quê |
|---|---|---|---|---|
| D1 | `PhoneService` em minúsculo | 70 + 23 | Padronizar para `Yes`/`No` | Sem isso, viram categorias diferentes. Os organizadores confirmaram que é só erro de grafia |
| D2 | `TotalCharges` nulo | 278 + 64 | Preencher com `MonthlyCharges` × `tenure` | A regra vale para 99% dos clientes; os 64 da inferência precisam de previsão; excluir perderia o sinal da ausência. Os organizadores consideraram razoável, como aproximação |
| D3 | `TotalCharges` nulo com `tenure` = 0 | 10 + 1 | 0 | Clientes novos, sem cobrança ainda; sai da própria regra |
| D4 | `tenure` = `unknown` | 19 + 4 | `TotalCharges` ÷ `MonthlyCharges`, arredondado; mediana do histórico no único caso sem os dois | `tenure` é das variáveis mais fortes; a mediana vem só do treino |
| D5 | Ausência de `TotalCharges` | 278 | Criar `fl_total_charges_ausente` | Quem não tinha o valor saiu mais (33,1% contra 26,4%, p = 0,016), mesmo dentro do contrato |
| D6 | Ausência de `tenure` | 19 | Não criar indicador | Poucos casos, sem diferença significativa (p = 0,21) |
| D7 | `TotalCharges` fora de ±20% da regra | 47 + 9 | Manter | Os organizadores explicaram: mudança de plano e promoções |
| D8 | Quebras de linha no comentário | 85 + 15 | Trocar por espaço | Deixa o texto limpo para o contraexemplo |

**Conferência (02):** nenhum problema restante, mesmo número de clientes, churn de 26,7% (igual ao bruto).

---

## 3. Vazamento: o texto do comentário

### D9 — Texto fora do modelo oficial ☑
- **Decisão:** o `CustomerFeedback` fica fora da ABT e do modelo oficial. O modelo com texto entra só como **contraexemplo** na apresentação, a partir da `gold_churn_texto`.
- **Por quê:**
  - quem saiu conta a decisão no passado ("I have decided to churn"); **nenhum** cliente que ficou usa essas expressões;
  - uma regra de uma linha sobre o texto acerta **98,9%**, com IV de 11,4, quase dez vezes o do contrato;
  - 88,7% dos textos citam a mensalidade exata, com centavos: parecem montados a partir da linha da base;
  - para o negócio, prever quem já escreveu "decidi cancelar" não gera nenhuma ação de retenção.
- **Evidência:** 03, seção 7.3; 05, seção 3.3 (AUC de 0,993 com o texto, contra 0,841 sem).
- **Em aberto:** a organização ainda não disse se o texto foi coletado antes ou depois do cancelamento. Se for antes, reavaliamos.

---

## 4. Variáveis (sugestões para a modelagem)

### D10 — Serviços como sim/não ◐
- **Sugestão:** usar os serviços na versão `_bin` (tem = 1, não tem = 0), **sempre junto com** `InternetService`.
- **Por quê:** "No internet service" repete a `InternetService` em seis colunas. A associação entre os serviços cai de 0,71–0,77 para 0,04–0,43 entre quem tem internet. Numa regressão logística, as dummies "No internet service" seriam colineares (repetidas sete vezes).
- **Achado do 04:** entre quem tem internet, segurança online (IV 0,40) e suporte técnico (0,39) separam bem; backup (0,17) e proteção de aparelho (0,13), médio; **streamings, nada** (0,00 e 0,01).
- **Na ABT:** as duas versões, original e `_bin`.

### D12 — `MonthlyIncome` ◐
- **Sugestão:** descartar.
- **Por quê:** IV de 0,004. A distribuição é quase uniforme e não se relaciona com nenhuma variável: parece gerada. Os organizadores disseram que é de uma base externa, sem garantia de precisão, e que pode ser ignorada.

### D15 — `gender`, `PhoneService`, `MultipleLines` ◐
- **Sugestão:** descartar.
- **Por quê:** IV abaixo de 0,02 (o churn varia só de 25% a 29% entre as categorias). `PhoneService` e `MultipleLines` também se repetem (V = 1,00). Sexo é uma variável sensível para uma decisão sobre o cliente.

### D16 — `MonthlyCharges` e `TotalCharges` ◐
- **Sugestão:** usar `MonthlyCharges` **ou** `mensalidade_relativa_pacote` (candidatas) e descartar `TotalCharges`.
- **Por quê:** a mensalidade repete o tipo de internet (η = 0,91); o total é quase mensalidade × meses (ρ = 0,89 com `tenure`). A `mensalidade_relativa_pacote` (preço ÷ média do mesmo tipo de internet, aprendida só no treino) separa o preço do pacote.

### D19 — Seleção de variáveis ☑
- **Decisão (11/11):** as 41 colunas do 05 (seções 2 e 3, código do Antonio): saem as 6 categóricas redundantes (ficam as versões `_bin`) e 12 variáveis por duplicata exata, versão repetida do tempo de casa ou falta de associação após a correção FDR (`gender`).
- **Conferência com os métodos da aula (05, seções 4 e 5):** as 9 recomendadas (`Contract`, `tenure`, `InternetService`, `OnlineSecurity_bin`, `TechSupport_bin`, `PaperlessBilling`, `Dependents`, `SeniorCitizen`, `Partner`) + `new_monthly_customer` + `is_electronic_check`.
- **Como:** regressão logística, validação cruzada de 5 dobras, seleção para frente por AUC, uma variável por grupo de alternativas, parando com ganho abaixo de 0,002.

| Modelo | AUC |
|---|---|
| Regra sem modelo (mensal e cheque eletrônico) | 0,678 |
| As 9 recomendadas | 0,834 |
| **Seleção sugerida (11)** | **0,841** |
| Todas as 30 recomendadas e candidatas | 0,843 |
| Seleção + texto (vazamento) | 0,993 |

- **Repetição:** VIF máximo de 2,75 (aceitável).
- **Quase entraram:** `MonthlyCharges`, `fl_total_charges_ausente`, `IsHighRiskContract`.
- **Encontro (05, seção 6):** as 11 variáveis da conferência estão todas dentro das 41 (`is_electronic_check` pela coluna equivalente `PaymentMethod_Electronic check`).

### D21 — Modelo final ☑
- **Decisão (11/11):** regressão logística Lasso, C = 0,3, classes balanceadas, sobre as 41 colunas, escolhida entre seis modelos pela consistência entre treino, teste e base total (06). No teste: ROC-AUC 0,830, F1 0,624, recall 78%, precisão 52%. Detalhes e números no `DOC_MODELO.md`.
- **Mudança em relação à execução original do Antonio:** lá a regra escolheu a Ridge (C = 0,03). Com o treino ordenado por `customerID` antes da separação, os clientes do teste mudaram e a Lasso passou à frente por 0,003 no Score. O método e a regra são os mesmos; a decisão segue a regra.
- **MLflow:** execução `dabb7c50091f4264b45767f994fb6f29`, modelo `models:/m-2dd8f256aa384a98bf46d77f84ff80eb`.
- **Na apresentação (12/11):** o grupo apresenta a Ridge (C = 0,03, limiar 0,4944, execução do Antonio), que também alimenta o app Central de relacionamento. Na mesma separação, Ridge e Lasso dão a mesma fila (222 dos 225 clientes do topo em comum, 99% do Sim/Não igual); comparação no `DOC_MODELO.md`, seção 4b.
- **Atenção:** o balanceamento infla a probabilidade (média perto de 41% para 27% de churn real). Para ordenar e para o Sim/Não não muda nada.

### D22 — Limiar ☑
- **Decisão (11/11):** 0,5046, o limiar que maximiza o F1 nas probabilidades fora da dobra do treino (06, 2.7). O KS máximo cai no score de 0,48, perto dele.

### D20 — Segmentação ◐
- **Sugestão:** K-means nas 17 variáveis de comportamento, sem o churn, cruzado com risco × valor (07). Cinco segmentos (silhueta 0,21): S1 fibra no contrato mensal com pouca proteção (55% de churn, 41% da receita, 62% dos que saíram), S2 DSL no contrato mensal e clientes novos (32%), S3 contrato anual (15%), S4 só telefonia (7%) e S5 fiéis de dois anos (5%).
- **Na inferência:** 398 clientes para "salvar já" (risco alto e mensalidade alta), 369 deles no S1.

---

## 5. Entrega

### D13 — Arquivo de previsão com 1.409 linhas ☑ (a confirmar)
- **Decisão:** uma linha por `customerID` da inferência.
- **Por quê:** o slide fala em 1.461, mas isso são linhas físicas do arquivo; 15 comentários ocupam mais de uma linha. Os clientes são 1.409.
- **Conferência final:** a taxa de "Yes" ficou em 40,5%, acima dos 27% de churn real, por causa do balanceamento e do limiar no máximo do F1 (recall de 78%). Treino, teste e inferência têm a mesma taxa prevista (40%), o que confirma a ausência de drift.

### D23 — Arquivo da entrega ☑
- **Como:** o 08 lê a `gold_churn_inferencia_scored`, põe na ordem do `inference.csv`, troca 1/0 por Yes/No, grava `prediction_grupo4_<timestamp>.csv` na raiz do repositório e confere 8 regras relendo o arquivo do disco.
- **Resultado (11/11):** as 8 regras deram `True`; 571 de 1.409 com Yes (40,5%).
- **Falta:** conferir os nomes das colunas com o `NOTEBOOK.ipynb` oficial.

---

## 5b. Depois da entrega

### D24 — Monitoramento do modelo ◐
- **Proposta (12/11):** a cada carteira pontuada, o 09 compara o que o modelo recebe e devolve com o que ele viu: PSI de 9
  variáveis e das notas (atenção a partir de 0,10, alerta a partir de 0,25), taxa de Yes (tolerância de ±5 e ±10 pontos),
  reprodução pelo MLflow e qualidade dos dados. Cada indicador aceso vira uma ação no app (acompanhar, investigar,
  retreinar, parar).
- **Evidência (12/11):** carteira de novembro toda estável (PSI máximo 0,009; 40,5% de Yes contra 39,8% no teste; MLflow
  reproduz com diferença 0). Lote simulado com peso 3 na fibra mensal: segmento em alerta (0,291), internet, notas,
  mensalidade e contrato em atenção, taxa de Yes de 59,9%. O alarme acende onde a carteira mudou e só lá.
- **Tabelas:** `gold_churn_monitoramento`, `gold_churn_monitoramento_distribuicao`, `gold_churn_fila_retencao`.

### D25 — Motor de atendimento ◐
- **Proposta (12/11):** levar o modelo para a ligação. O 10 exporta os parâmetros do modelo oficial para o app, que
  calcula a nota de qualquer ficha de cliente, explica os motivos por tema e monta a escada de ofertas (principal, sem
  fidelidade de dois anos, sem mudar o contrato). Para quem ainda não é cliente, compara pacotes.
- **Evidência (12/11):** 6 conferências `True` (variáveis iguais à gold, nota igual à publicada e à do pipeline, diferença
  de nota 0, decis iguais); tabela de preço explica 99,9% da mensalidade (telefone R$ 20, DSL R$ 25, fibra R$ 50,
  proteção R$ 5, streaming R$ 10). Pela nota do modelo, a oferta principal tira 476 dos 571 da zona de risco; sem mudar
  o contrato, 110. É associação do modelo, não retenção garantida: medir com teste.
- **Campanha:** com a taxa real de churn por decil no teste, o app calcula o tamanho de campanha de maior lucro. Com
  R$ 15 por contato, 30% de aceite e 10% de desconto em 12 meses, o ótimo são 705 clientes (cerca de R$ 58,6 mil), e o
  limiar do modelo (571) dá cerca de R$ 57,8 mil.
- **Tabela:** `gold_churn_ofertas`; arquivos do app: `modelo_motor.json`, `clientes_atendimento.csv`, `ganho_teste.csv`.

---

### D26 — Leitura do comentário por LLM ◐
- **Proposta (12/11, Lucas):** o notebook 11 lê cada comentário com `ai_query` (`system.ai.gpt-oss-20b`) e devolve a situação relatada, o sentimento e os motivos, com evidência literal e validação técnica.
- **Por quê:** o comentário não pode entrar no modelo (D9), mas diz à operadora como abrir a conversa.
- **Evidência (12/11):** 7.043 textos, nenhum erro de API; 5.432 válidos tecnicamente e 1.611 com alerta, que ficam visíveis mas não orientam o encaminhamento.

---

## 6. Respostas dos organizadores (Carlos, Databricks, 10/11)

| Tema | Resposta | Decisões ligadas |
|---|---|---|
| Moeda | R$ em todo o dataset (o "$" do texto não vale) | Metadados |
| `SeniorCitizen` | 1 = idoso; considerar 65 anos ou mais | Metadados |
| `MonthlyIncome` | Renda familiar mensal, em R$, de base externa, sem garantia de precisão; pode ser ignorada | D12 |
| `tenure` | 72 meses é teto real (a empresa tem cerca de 7 anos) | D4 |
| `MonthlyCharges` | Último mês faturado, com taxas; para quem saiu, o último antes do cancelamento | D16 |
| `TotalCharges` | Soma das mensalidades; o preço muda com plano e promoções; preencher por mensalidade × meses é razoável, como aproximação | D2, D7 |
| `PhoneService` | `yes`/`no` minúsculo é só erro de padronização | D1 |

---

## 7. Em aberto

**Para a organização**
- O comentário foi escrito antes ou depois do cancelamento? (D9)
- Por que alguns clientes não têm `TotalCharges`? (D5)
- O `Prediction.csv` tem 1.409 linhas? Com probabilidade, classe Yes/No ou as duas? (D13)
- Qual métrica avalia a entrega?
- Como histórico e inferência foram separados (sorteio ou data)?
- Qual o custo e a taxa de sucesso de uma ação de retenção? (ponto de corte)

**Para a modelagem**
- Ponto de corte pela regra p* = c ÷ (s × V) (notebook 00), se a organização der custo e taxa de sucesso.
- Conferir o arquivo do 08 com o `NOTEBOOK.ipynb` oficial (nomes das colunas, Yes/No ou 1/0).
- Avisar o grupo da troca da Ridge pela Lasso (D21).

**Para o grupo**
- Permissão de escrita de todos em `workspace.terra_signal`.
- O que entra na apresentação: perfil de risco, gráfico do vazamento, gráfico do PSI.
