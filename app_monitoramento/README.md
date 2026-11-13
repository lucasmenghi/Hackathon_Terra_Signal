# Central de retenção — Terra Signal · Grupo 4

Aplicativo em Streamlit que leva o modelo de churn para a ligação e o acompanha depois da entrega. A página
Atendimento usa o motor do notebook `10_atendimento` (o mesmo cálculo do modelo do pipeline, a regressão logística Lasso,
conferido lá com diferença de nota zero); as outras leem as tabelas que o notebook `09_monitoramento` grava.

| Página | Pergunta |
|---|---|
| Atendimento | Receptivo: o cliente na linha, com o resumo dele em "X em cada 10", o porquê, o que ele contou, o histórico de contatos e a escada de ofertas. Ativo: a lista de ligações da carteira, separada em retenção, recuperação e fidelização e ordenada pela receptividade. Novo cliente: que pacote oferecer? Registro com roteiro, missões do dia, XP e conquistas |
| Plano de marketing | Que ofertas a central pode fazer, com que fala, até quando e para quais segmentos? E quantos clientes da fila o plano tira da zona de risco? |
| Campanha de retenção | Quantos clientes contatar para ter o maior lucro, com o custo, o aceite e o desconto informados? |
| Pergunte aos dados | Perguntas em português, respondidas pelo Genie (espaço Terra Signal · Retenção) |
| Saúde do modelo | O modelo está devolvendo o que devolvia? (semáforo de cada lote) |
| Deriva das variáveis | O que mudou na carteira em relação ao treino? (PSI e distribuição faixa a faixa) |
| Fila de retenção | Quem procurar primeiro, e com que oferta? |
| Ficha do modelo | O que está em produção e quando retreinar? |

Os gráficos seguem o *Better Data Visualizations* (Jonathan Schwabish): título com a conclusão, uma cor de destaque
e cinza para o contexto, rótulos direto nos dados em vez de legenda, linhas de referência nomeadas e fonte no rodapé.
Cada gráfico vem com a caixa "Como ler": onde olhar, o que observar, o que comparar e o achado.

## Estrutura

```
app_monitoramento/
├── app.py                      ← Home
├── app.yaml                    ← configuração do Databricks App
├── requirements.txt
├── .streamlit/config.toml      ← tema claro com a cor do projeto
├── config/theme.py             ← CSS, header, cards, KPIs, "como ler"
├── utils/dados.py              ← leitura: SQL Warehouse ou CSV
├── utils/graficos.py           ← gráficos (plotly)
├── utils/pagina.py             ← abertura padrão das páginas e filtro de lote
├── motor/                      ← motor de atendimento: variáveis derivadas, nota do modelo, ofertas, leitura do relato
├── pages/                      ← as oito páginas
├── assets/                     ← logo e ilustrações (ver assets/LEIA-ME.md)
└── dados/                      ← CSV e JSON gravados pelos notebooks 09 (seção 5) e 10 (seção 5)
```

## Rodar localmente

```powershell
pip install -r requirements.txt
streamlit run app.py
```

Sem a variável `DATABRICKS_WAREHOUSE_ID`, o app lê os CSV de `dados/`. A pasta já vem com um retrato do teste local;
rodar o notebook 09 no Databricks atualiza esses arquivos.

## Publicar como Databricks App

1. Rodar os notebooks `09_monitoramento` e `10_atendimento` até o fim (gravam as tabelas, os CSV, o `modelo_motor.json` e o
   `relatos_inferencia.csv`). Como alternativa, o notebook `instalar_app` grava o código do app e o arquivo dos relatos.
2. Em **Compute → Apps → Create app → Custom**, dar um nome (por exemplo `monitoramento-churn`).
3. Em **App resources**, adicionar um **SQL Warehouse** (o *Serverless Starter Warehouse* do Free Edition), com a
   chave `sql-warehouse` e permissão *Can use*. É ele que o `app.yaml` passa como `DATABRICKS_WAREHOUSE_ID`.
4. Dar ao *service principal* do app permissão de leitura no schema: no Catalog, em `workspace.terra_signal`,
   **Permissions → Grant →** o principal do app com `USE CATALOG`, `USE SCHEMA` e `SELECT`.
5. **Deploy**, apontando para a pasta `app_monitoramento` no Workspace (a pasta Git do grupo).

**Genie (página Pergunte aos dados):** em App resources, adicionar **Genie space** (Terra Signal · Retenção), permissão
*Can run*, chave `genie-space`; o service principal do app precisa de `SELECT` em `workspace.terra_signal` (passo 4).

Se o SQL Warehouse ou a permissão não estiverem configurados, o app avisa na barra lateral e usa os CSV de `dados/`.
No Free Edition, cada app roda por até 24 horas depois de iniciado e para sozinho; para religar, use **Start** na
página do app.
