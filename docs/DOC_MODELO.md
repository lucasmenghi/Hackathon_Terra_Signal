# Documentação — Seleção de variáveis e modelagem (notebooks `05_selecao_variaveis` e `06_modelagem`)

**Projeto:** Hackathon ASN · Databricks — Grupo 4 · **Caso:** Terra Signal (churn de telecom)
**Objetivo:** prever quem vai cancelar e priorizar a retenção pelos clientes de maior risco.

O modelo é o do notebook `modelo-antonio`, com o mesmo código, reorganizado no padrão dos outros notebooks do projeto em duas partes: a preparação e os testes estatísticos estão no `05_selecao_variaveis` (seções 2 e 3), e os modelos, a avaliação e a produção no `06_modelagem` (seções 2 a 6). O 05 grava a separação treino/teste e as listas de variáveis, e o 06 reconstrói exatamente as mesmas bases. A organização inclui perguntas de negócio, teoria antes de cada etapa, "como ler" depois de cada resultado e checklist.

**Execução oficial:** 11/11, no Databricks, conta do André, com o treino ordenado por `customerID` antes da separação (os números se repetem em qualquer conta).

**O que é do Antonio e o que mudou.** A preparação, os testes, os seis modelos, a regra de consistência que escolhe o modelo, o limiar, a avaliação e o pipeline de produção são o método do Antonio, sem mudança. O grupo ajustou: (1) a ordenação e a gravação da separação treino/teste (`gold_churn_split`); (2) `n_jobs=1` na busca, porque os processos paralelos travam no Serverless; (3) os parâmetros do MLflow lidos do modelo escolhido; (4) as respostas e os "como ler". Na execução original do Antonio, a regra escolheu a **Ridge** (C = 0,03, limiar 0,4944, ROC-AUC 0,845 no teste). Na execução oficial, com a separação ordenada, a mesma regra escolheu a **Lasso** (C = 0,3, limiar 0,5046, ROC-AUC 0,830), com a Ridge a 0,003 de distância no Score: as duas logísticas estão praticamente empatadas, e a decisão segue a regra.

---

## Perguntas de negócio e respostas

| # | Pergunta | Resposta | Seção |
|---|---|---|---|
| M1 | Que variáveis entram no modelo, e por quê? | 41 variáveis: saem as 6 categóricas redundantes e 12 variáveis por duplicata exata, versão repetida do tempo de casa ou falta de associação (`gender`, após a correção para múltiplos testes) | 05: 2 e 3 |
| M2 | Qual algoritmo prevê melhor o churn? | Regressão logística Lasso (C = 0,3, classes balanceadas), escolhida pela consistência entre treino, teste e base total; a Ridge ficou a 0,003 | 06: 2 |
| M3 | A partir de que probabilidade dizemos que o cliente vai sair? | 0,5046, o limiar que maximiza o F1 nas probabilidades fora da dobra do treino | 06: 2.7 |
| M4 | O modelo funciona em clientes que ele não viu? | Sim: no teste, ROC-AUC de 0,830, F1 de 0,624, recall de 78% e precisão de 52%, perto do treino (F1 0,641) | 06: 3 |
| M5 | Se só der para ligar para parte da carteira, quanto ganhamos? | Os 20% de maior risco concentram 48% dos churners (lift acumulado de 2,41); o decil 1 tem 76% de churn | 06: 4 |
| M6 | O que mais aumenta e diminui o risco de sair? | Aumentam: cheque eletrônico, internet sem suporte, fibra, cliente idoso. Reduzem: contrato de dois anos e anual, tempo de casa, segurança online. Preço e número de serviços andam com a fibra e se leem juntos | 06: 5 |
| M7 | Quantos clientes da carteira estão em risco, e onde está o resultado? | 571 de 1.409 (40,5%) acima do limiar; tabelas `gold_churn_abt_scored` e `gold_churn_inferencia_scored`, e o pipeline no MLflow | 06: 6 |

---

## 1. Dados de entrada (05, seção 1)

| Tabela | Formato |
|---|---|
| `workspace.terra_signal.gold_churn_treino` | 5.634 clientes × 51 colunas, com `Churn` (1/0) |
| `workspace.terra_signal.gold_churn_inferencia` | 1.409 clientes × 50 colunas, sem `Churn` |
| `workspace.terra_signal.gold_churn_split` | Quem é treino (4.507) e quem é teste (1.127), com a ordem; gravada no 05 e lida no 06 |
| `workspace.terra_signal.gold_churn_variaveis_modelo` | As listas de variáveis (6 redundantes, 11 categóricas, 12 retiradas, 41 do modelo) |
| `workspace.terra_signal.gold_churn_selecao` | A conferência com os métodos da aula (11 variáveis), que cabe dentro das 41 |

A ABT vem da camada gold (notebooks 01 a 04): sem valores ausentes, com `TotalCharges` preenchido (marcado em `fl_total_charges_ausente`) e com as variáveis derivadas.

## 2. Preparação das variáveis (05, seção 2)

| Etapa | O que faz | Resultado |
|---|---|---|
| Categóricas redundantes | Retira `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV` e `StreamingMovies`, que repetem as versões `_bin` | 51 → 45 colunas |
| Dummies | `gender`, `Partner`, `Dependents`, `PhoneService`, `MultipleLines`, `InternetService`, `Contract`, `PaperlessBilling`, `PaymentMethod`, `TenureCohort` e `tenure_group` viram colunas 0/1 (`drop_first=True`; a referência é a primeira categoria em ordem alfabética) | 21 dummies; 45 → 55 colunas; 53 preditoras |
| Treino e teste | `train_test_split` 80/20, estratificado pelo `Churn`, `random_state=42` | Treino 4.507 (26,69% de churn) · teste 1.127 (26,71%) |

Todas as escolhas seguintes (testes, retirada de variáveis, hiperparâmetros e limiar) usam **só o treino**. O teste fica separado até a avaliação final.

## 3. Testes estatísticos e retirada de variáveis (05, seção 3)

| Teste | Uso | Destaques |
|---|---|---|
| Pearson entre preditoras | Pares com \|r\| > 0,7: candidatos a redundância | Versões do tempo de casa, contagens de serviços |
| Pearson com o `Churn`, com p-valor | Força e direção de cada variável | `is_monthly_contract` +0,405; `IsHighRiskContract` +0,358; `tenure` −0,351; `HasFiberOpticWithoutTechSupport` +0,349 |
| Qui-quadrado (Fisher com esperado < 5) + V de Cramér | Variáveis 0/1 | `is_monthly_contract`: V = 0,405; `gender_Male`: V = 0,011 |
| Mann-Whitney | Variáveis contínuas, sem supor normalidade | Medianas de quem sai e de quem fica |
| Correção FDR (Benjamini-Hochberg) | Ajusta os p-valores dos 53 testes | `gender_Male`: p-ajustado 0,467 (não significativa); 9 variáveis não significativas, das quais só `gender_Male` sai por esse motivo |
| Duplicatas exatas (`np.allclose`) | Confirma cálculos exatos | `income_after_charges` e `total_addons`: 100% iguais ao cálculo; `average_monthly_charges`: difere só nos 9 clientes com `tenure` = 0 |

**As 12 variáveis retiradas:**

| Variável | Motivo |
|---|---|
| `tenure_years` | `tenure` em anos |
| `is_electronic_check` | Igual a `PaymentMethod_Electronic check` |
| `PhoneService_Yes` | Inverso de `MultipleLines_No phone service` |
| `tenure_group_13-24` | Igual a `TenureCohort_13-24` |
| `income_after_charges` | `MonthlyIncome` − `MonthlyCharges` |
| `total_addons` | `n_protecao` + `n_streaming` |
| `average_monthly_charges` | `TotalCharges` ÷ `tenure` |
| `tenure_group_7-12`, `tenure_group_25-48`, `tenure_group_49+` | Segunda discretização de `tenure` (no Lasso, deu sinais opostos aos de `TenureCohort`) |
| `is_monthly_contract` | 1 − `Contract_One year` − `Contract_Two year` |
| `gender_Male` | Sem associação depois da correção FDR; efeito desprezível |

As dummies não significativas que fazem parte de blocos que ficam (por exemplo, `TenureCohort_13-24`) foram mantidas, para não quebrar a codificação da categoria de referência.

**Conferência com os métodos da aula (05, seções 4 a 6).** Seleção para frente por AUC (validação cruzada 5 × 5), *stepwise* por AIC, BIC e p-valor, VIF e intervalos dos coeficientes: 11 variáveis, AUC de 0,841, VIF máximo de 2,75. As 11 estão dentro das 41 (11 de 11, ocupando 13 colunas). Os dois caminhos chegam às mesmas variáveis principais.

**41 variáveis finais:**

| Tema | Variáveis |
|---|---|
| Fidelidade e tempo de casa (6) | `tenure`, `TenureCohort_6-12`, `TenureCohort_13-24`, `TenureCohort_25+`, `is_new_customer`, `new_monthly_customer` |
| Contrato (3) | `Contract_One year`, `Contract_Two year`, `IsHighRiskContract` |
| Serviços e pacotes (16) | `InternetService_Fiber optic`, `InternetService_No`, `MultipleLines_Yes`, `MultipleLines_No phone service`, `OnlineSecurity_bin`, `OnlineBackup_bin`, `DeviceProtection_bin`, `TechSupport_bin`, `StreamingTV_bin`, `StreamingMovies_bin`, `TotalServicesSubscribed`, `no_support_with_internet`, `HasFiberOpticWithoutTechSupport`, `n_protecao`, `n_streaming`, `mensalidade_relativa_pacote` |
| Pagamento (5) | `PaymentMethod_Credit card (automatic)`, `PaymentMethod_Electronic check`, `PaymentMethod_Mailed check`, `PaperlessBilling_Yes`, `pagamento_automatico` |
| Financeiro (5) | `MonthlyCharges`, `TotalCharges`, `fl_total_charges_ausente`, `ChargesRatio`, `charge_difference` |
| Perfil (6) | `SeniorCitizen`, `Partner_Yes`, `Dependents_Yes`, `has_family`, `MonthlyIncome`, `IncomeCommitment` |

## 4. Comparação de modelos e limiar (06, seção 2)

- **Validação cruzada:** `StratifiedKFold(5, shuffle=True, random_state=42)`, só no treino. O critério da busca é o F1; também são registrados precisão, recall, ROC-AUC e PR-AUC.
- **Desbalanceamento:** as logísticas usam `class_weight="balanced"`; o XGBoost e o CatBoost usam `scale_pos_weight` = 2,7465 (a razão de classes no treino).
- **Pré-processamento dentro do pipeline:** `SimpleImputer(median)` e `StandardScaler` (este só nas logísticas), ajustados só nas dobras de treino.

| Modelo | Busca | Hiperparâmetros testados |
|---|---|---|
| Logística Lasso (L1) | Grade | `C` ∈ {0,01; 0,03; 0,1; 0,3; 1; 3; 10; 100}, solver `saga` |
| Logística Ridge (L2) | Grade | Mesma grade de `C`, solver `lbfgs` |
| Logística Elastic Net | Grade | `C` (8 valores) × `l1_ratio` ∈ {0,10; 0,25; 0,50; 0,75; 0,90} |
| *Random forest* | Aleatória (40) | `n_estimators` 200 a 600, `max_depth`, `min_samples_split`, `min_samples_leaf`, `max_features`, `class_weight` |
| XGBoost | Aleatória (40) | `n_estimators`, `max_depth`, `learning_rate`, `subsample`, `colsample_bytree`, `min_child_weight`, `gamma`, `reg_alpha`, `reg_lambda`, `scale_pos_weight` |
| CatBoost | Aleatória (40) | `iterations`, `learning_rate`, `depth`, `l2_leaf_reg`, `subsample`, `border_count`, `scale_pos_weight` |

**Limiar de decisão (M3):** para cada modelo, as probabilidades fora da dobra do treino (`cross_val_predict`) são varridas com `precision_recall_curve`. O limiar escolhido é o de maior F1, e ele fica congelado: só depois é aplicado ao teste, à base total e à inferência. O teste nunca participa da escolha.

| Modelo | Limiar |
|---|---|
| **Logística Lasso (escolhido)** | **0,5046** |
| Logística Ridge | 0,5026 |
| Logística Elastic Net | 0,4995 |
| XGBoost | 0,5031 |
| *Random forest* | 0,5021 |
| CatBoost | 0,5441 |

**Validação cruzada (treino):**

| Modelo | Precisão | Recall | F1 | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|
| Logística Elastic Net | 0,530 | 0,807 | 0,640 | 0,846 | 0,662 |
| Logística Ridge | 0,534 | 0,797 | 0,639 | 0,846 | 0,660 |
| **Logística Lasso** | 0,530 | 0,806 | 0,639 | 0,847 | 0,661 |
| XGBoost | 0,523 | 0,814 | 0,637 | 0,845 | 0,656 |
| *Random forest* | 0,562 | 0,729 | 0,634 | 0,841 | 0,652 |
| CatBoost | 0,534 | 0,777 | 0,633 | 0,844 | 0,658 |

A diferença de F1 entre o primeiro e o último (0,007) é menor que o desvio entre as dobras (0,016 a 0,024): pela validação cruzada, os seis estão empatados.

**Escolha pela consistência** (Score = F1 médio entre treino fora da dobra, teste e base total − amplitude do F1):

| Modelo | F1 treino | F1 teste | F1 total | Amplitude | Score |
|---|---|---|---|---|---|
| **Logística Lasso** | 0,641 | 0,624 | 0,637 | 0,017 | **0,617** |
| Logística Ridge | 0,640 | 0,621 | 0,640 | 0,019 | 0,615 |
| Logística Elastic Net | 0,641 | 0,621 | 0,636 | 0,019 | 0,613 |
| XGBoost | 0,637 | 0,624 | 0,647 | 0,023 | 0,613 |
| CatBoost | 0,637 | 0,624 | 0,691 | 0,067 | 0,584 |
| *Random forest* | 0,634 | 0,622 | 0,712 | 0,090 | 0,566 |

As árvores ficam parecidas na validação cruzada, mas inflam o F1 na base total (que inclui os clientes do treino que elas decoraram), um sinal de sobreajuste, e por isso ficam atrás na consistência.

**Seleção feita pelo próprio modelo:** a Lasso zera 11 das 41 colunas e fica com 30 (o Elastic Net zera 6, todas entre as 11). Entre as zeradas: `TotalCharges`, `has_family`, `n_protecao`, `pagamento_automatico`, `TechSupport_bin` e `InternetService_No`.

## 4b. Ridge × Lasso na mesma separação

As duas logísticas regularizadas empataram. A apresentação e o app Central de relacionamento usam a **Ridge** (execução
do Antonio); o pipeline destes notebooks registra a **Lasso**. Para mostrar que a escolha não muda a fila, as duas
foram treinadas de novo na separação fixa (4.507 de treino, 1.127 de teste), com o mesmo método:

| No teste (1.127 clientes) | Ridge (L2, C = 0,03) | Lasso (L1, C = 0,3) |
|---|---|---|
| ROC-AUC | 0,830 | 0,830 |
| F1 / recall / precisão | 0,621 / 0,771 / 0,520 | 0,624 / 0,777 / 0,521 |
| Limiar (maior F1 fora da dobra) | 0,5026 | 0,5046 |
| Captura nos 20% de maior risco | 48,5% | 47,8% |
| Churn real no decil 1 | 76,1% | 76,1% |
| Variáveis zeradas | 0 | 11 |

- **Mesma ordem de clientes:** correlação de Spearman de 0,999 entre as notas; 222 dos 225 clientes do topo de 20% em
  comum; 99,2% dos clientes com o mesmo Sim/Não.
- **Por que a Ridge na apresentação:** ela mantém todas as variáveis com peso pequeno e divide o peso entre as que
  andam juntas. Mensalidade e fibra (correlação de 0,79): a Lasso dá +0,49 à mensalidade e +0,10 à fibra; a Ridge,
  +0,20 e +0,25. Os sinais ficam mais fáceis de explicar ao negócio.
- **Por que os números dos slides são outros (ROC-AUC 0,845, 51,8% no topo):** vêm da separação original do Antonio,
  com outros clientes no teste. O ROC-AUC fica entre 0,83 e 0,845 conforme a separação.

## 5. Avaliação na base de teste (06, seção 3)

| Métrica | Valor |
|---|---|
| Acurácia | 0,750 |
| Acurácia balanceada | 0,759 |
| Precisão (churn) | 0,521 |
| Recall (churn) | 0,777 |
| Especificidade | 0,740 |
| F1 (churn) | 0,624 |
| ROC-AUC | 0,830 |
| PR-AUC | 0,641 |
| KS | 0,523 (no score de 0,48) |
| Log loss | 0,509 |
| Brier | 0,172 |
| MCC | 0,467 |
| Kappa de Cohen | 0,447 |

**Matriz de confusão (limiar de 0,5046):** 611 não churn corretos, 215 alarmes falsos, 67 churners perdidos e 234 churners capturados.
**Consistência sem retreino:** a amplitude entre treino, teste e total é de 0,012 na precisão, 0,025 no recall e 0,017 no F1. Todas ficam abaixo do limite de referência de 0,10.
**Base total (5.634):** 2.261 previstos como churn (40,1%), com 1.199 dos 1.504 que saíram (recall de 80%).

## 6. KS e lift (06, seção 4)

| Decil | Taxa de churn | Lift | Captura acumulada |
|---|---|---|---|
| D1 (10% de maior risco) | 76,1% | 2,85 | 28,6% |
| D2 | 52,2% | 1,95 | 48,2% |
| D3 | 47,3% | 1,77 | 65,8% |
| D4 | 31,9% | 1,19 | 77,7% |
| D5 | 20,4% | 0,76 | 85,4% |
| D6 a D10 | de 14,3% a 1,8% | de 0,53 a 0,07 | 100% |

Lift acumulado nos 20% de maior risco: 2,41 (48% dos churners).

## 7. Leitura de negócio (06, seção 5)

| Tema | Peso no modelo (soma dos \|coeficientes\| padronizados) |
|---|---|
| Fidelidade e tempo de casa | 31,7% |
| Serviços e pacotes | 26,0% |
| Contrato | 20,4% |
| Financeiro | 10,5% |
| Pagamento | 7,5% |
| Perfil do cliente | 4,1% |

- **Reduzem o risco:** `Contract_Two year` (−0,67), `tenure` (−0,56), `TenureCohort_25+` (−0,39), `TenureCohort_13-24` (−0,32), `Contract_One year` (−0,31), `TenureCohort_6-12` (−0,26), `OnlineSecurity_bin` (−0,12).
- **Aumentam:** `PaymentMethod_Electronic check` (+0,15), `no_support_with_internet` (+0,12), `InternetService_Fiber optic` (+0,10), `SeniorCitizen` (+0,09), `PaperlessBilling_Yes` (+0,08).
- **Lidas em conjunto:** `MonthlyCharges` (+0,49) e `mensalidade_relativa_pacote` (−0,40), `n_streaming` (+0,34) e `MultipleLines_Yes` (+0,14) andam com o tipo de internet (correlação de 0,79 entre mensalidade e fibra). Um por um, os sinais não têm leitura de negócio; é a mesma multicolinearidade que a 5.5c do 05 mostra.

**A história:** tempo de casa e contrato somam mais da metade do peso. Quem fica tem casa longa e contrato anual ou de dois anos; quem sai é novo, mensal, paga por cheque eletrônico e tem fibra sem suporte. O risco vem mais do que o cliente contrata e de como paga do que de quem ele é (o perfil pesa 4%).

## 8. Produção: pipeline, tabelas e MLflow (06, seção 6)

**Pipeline de produção.** Um único `Pipeline` do scikit-learn recebe a base no formato da ABT e devolve a probabilidade. Ele faz as limpezas na ordem:
1. retira as 6 categóricas redundantes;
2. cria as dummies;
3. separa as colunas numéricas;
4. retira as 12 variáveis;
5. converte os valores para número;
6. alinha as 41 colunas;
7. aplica o modelo congelado (imputação, padronização e Lasso).

O pipeline foi validado com `np.allclose`: reproduz exatamente as bases de treino e teste e as probabilidades da avaliação.

**Tabelas publicadas em `workspace.terra_signal`:**

| Tabela | Linhas | Colunas novas |
|---|---|---|
| `gold_churn_abt_scored` | 5.634 | `Probabilidade_Churn`, `Churn_Previsto` (limiar 0,5046), `Base_Modelagem` (Treino ou Teste), `Decil_Risco` |
| `gold_churn_inferencia_scored` | 1.409 | `Probabilidade_Churn`, `Churn_Previsto`, `Decil_Risco` (decis da própria inferência) |

**Na tabela da ABT, as linhas `Treino` são previsões dentro da amostra** (o modelo viu esses clientes); só as linhas `Teste` medem o desempenho real.

**Inferência:** 571 clientes previstos como churn (40,5%). Os 281 clientes do top 20% formam a fila de priorização. O decil 1 tem 141 clientes, com probabilidade média de 0,89.

**MLflow:** o pipeline completo foi registrado com assinatura, exemplo de entrada e as métricas do teste. Os parâmetros gravados são lidos do modelo escolhido (Lasso, C = 0,3, `penalty` l1, `solver` saga, classes balanceadas, limiar 0,5046). Ele carrega com `mlflow.pyfunc.load_model('models:/m-2dd8f256aa384a98bf46d77f84ff80eb')` (execução `dabb7c50091f4264b45767f994fb6f29`, experimento `/Shared/terra_signal_churn`, id `2640294097585011`).

**Modelo escolhido (`gold_churn_modelo_info`):** uma linha com o modelo, o limiar, o número de variáveis e as métricas do teste, lida pelo 08.

## 9. Depois da entrega: monitoramento e atendimento (notebooks 09 e 10)

- **Monitoramento (09, D24):** a carteira de novembro está estável (PSI máximo 0,009; 40,5% de Yes contra 39,8% no teste) e o registro do MLflow reproduz as notas publicadas (diferença 0). Um lote simulado com mais fibra no contrato mensal acende o alarme nas variáveis certas.
- **Motor de atendimento (10, D25):** os parâmetros do modelo foram exportados para o app (`modelo_motor.json`) e conferidos: mesma nota, mesmos decis. O app explica cada nota por tema, monta a escada de ofertas e dimensiona a campanha pelo lucro, usando a taxa real de churn por decil no teste.
- **Registro do modelo:** experimento fixo `/Shared/terra_signal_churn`; o endereço fica em `gold_churn_modelo_info` (`model_uri`, `run_id`), lido pelo 09 e pelo 10.

## Decisões

| # | Decisão | Status |
|---|---|---|
| D21 | Modelo final: logística Lasso, C = 0,3, classes balanceadas, 41 variáveis (vencedora pela regra de consistência) | ☑ 11/11 |
| D22 | Limiar do Sim/Não: 0,5046 (maior F1 fora da dobra, no treino) | ☑ 11/11 |
| D23 | Arquivo da entrega: `prediction_grupo4_<data_hora>.csv`, conferido nas 8 regras (571 de 1.409 com Yes) | ☑ 11/11; falta comparar os nomes das colunas com o `NOTEBOOK.ipynb` oficial |
| D24 | Monitoramento do modelo (09) | ◐ 12/11 |
| D25 | Motor de atendimento e app (10) | ◐ 12/11 |
| D26 | Leitura do comentário por LLM para a central (11), fora do modelo | ◐ 12/11 |

## Limites

- **A probabilidade é uma nota de risco.** Com o balanceamento, a média prevista fica perto de 41% para 27% de churn real, e no grupo mais alto o modelo prevê cerca de 89% quando saem 76%. Para ordenar a fila e para o Sim/Não, isso não muda nada. Para números que multiplicam a probabilidade (perda esperada em R$), vale recalibrar antes. Por isso o notebook 07 (segmentação) usa a previsão Sim/Não, e não a probabilidade × mensalidade.
- **Receita em risco não é perda esperada.** No 07, a receita dos 571 clientes previstos como churn é de R$ 43.688 por mês (47% da carteira); com precisão de 52%, pouco mais da metade desse valor deve se perder.
- **Ordem das linhas (resolvido).** A separação treino/teste depende da ordem das linhas. O 05 ordena o treino por `customerID` antes de separar e grava a separação (`gold_churn_split`); o 06 a reconstrói. Os números se repetem em qualquer conta.

## Como reproduzir

Rodar no Databricks, de cima para baixo e nesta ordem: `05_selecao_variaveis` (grava `gold_churn_split` e `gold_churn_variaveis_modelo`), `06_modelagem` (a primeira célula instala XGBoost, CatBoost, statsmodels e seaborn e reinicia o Python; a busca de hiperparâmetros, célula 2.5, é a parte mais demorada), `07_segmentacao` (usa a `gold_churn_inferencia_scored`) e `08_entrega` (gera o `prediction_grupo4_<timestamp>.csv`).
