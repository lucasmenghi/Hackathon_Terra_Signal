# App Central de relacionamento (Python + FastAPI)

**Hackathon Databricks · Terra Signal · Grupo 4** · Autor: Lucas Menghi

O app abre direto na carteira dos **1.409 clientes da inferência**, ordenados do maior para o menor risco de churn. A
operadora filtra a fila, abre o perfil de um cliente e vê, numa tela só, a nota do modelo, os produtos que ele tem e a
leitura do comentário feita pela LLM (situação relatada, sentimento e motivos). Uma jornada de cinco missões ensina a
usar a central.

| O que | De onde vem |
|---|---|
| Nota de churn, previsão Sim/Não e decil de risco | Regressão logística Ridge (C = 0,03, limiar 0,4944), execução do Antonio. Arquivo `data/churn_scores.csv` |
| Situação relatada, sentimento e motivos do comentário | Notebook `11_feedback_llm_ai_query` (`ai_query` com `system.ai.gpt-oss-20b`). Arquivo `data/feedback_classifications.csv` |
| Dados do cliente (produtos, contrato, pagamento, comentário) | `data/history.csv` e `data/inference.csv`, cópias dos arquivos do hackathon |

Os arquivos são lidos na inicialização e conferidos (IDs únicos, notas entre 0 e 1, cobertura dos 7.043 clientes). Se
algo falhar, o app não sobe: não existe dado de exemplo inventado.

## O que a tela mostra

- **Ranking de prioridade:** os 1.409 clientes da inferência, maior nota primeiro. Filtros por ID, decil (D1 a D10),
  previsão (1 = vai sair, 0 = fica), sentimento do comentário e faixa de nota. Os filtros são aplicados no servidor
  antes da paginação.
- **Perfil do cliente:** nota, previsão e decil recebidos do modelo (sem recalcular); produtos e relacionamento; o
  comentário original e a leitura da LLM, com a evidência literal. Leituras com alerta técnico aparecem sinalizadas e
  não orientam o encaminhamento.
- **Próximo passo:** o encaminhamento sugerido por regras no notebook 11, a partir da leitura do comentário. Os botões de visita técnica, ofertas e
  plano abrem uma explicação: não executam nem gravam ações (não há integração com sistemas comerciais).
- **Minha jornada:** cinco missões pessoais (abrir um perfil, filtrar por decil, filtrar pela previsão, abrir a leitura
  do comentário e responder o que significa D1). O progresso fica no navegador (`localStorage`), sem dados de clientes.

## Números conferidos (12/11/2026)

| Item | Valor |
|---|---|
| Clientes da inferência na carteira | 1.409 (562 com previsão 1 e 847 com previsão 0) |
| Leituras do comentário | 7.043 (5.634 do histórico e 1.409 da inferência) |
| Válidas tecnicamente / com alerta | 5.432 / 1.611 (inferência: 1.077 / 332) |
| Testes automáticos | 10 testes de dados e integração passando (`python -m unittest discover -s tests -v`) |

## Publicar no Databricks Apps

1. Envie a pasta inteira para o workspace, preservando as subpastas: `main.py`, `repository.py`, `app.yaml` e
   `requirements.txt` na raiz, com `data/`, `static/`, `contracts/` e `tests/` ao lado. Os `.py` vão como arquivos, não
   como notebooks.
2. Em **Compute → Apps**, crie um app personalizado e aponte o *source code path* para essa pasta.
3. Faça o **Deploy**. O `app.yaml` roda `python main.py`; o servidor usa a porta `DATABRICKS_APP_PORT`.
4. Abra a URL do app e confira `/health` (status `ok` e os volumes) e a carteira com 1.409 clientes.

O modo atual não precisa de SQL Warehouse, token pessoal nem endpoint de IA: o app só lê os arquivos da pasta `data/`.
O acesso é controlado pelas permissões do próprio Databricks Apps.

## Rodar localmente

```text
python -m venv .venv
# Windows: .venv\Scripts\activate   ·   Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Abra `http://localhost:8012`. A variável `DATA_DIR` aponta para outra pasta com os mesmos arquivos.

## Atualizar os resultados

- **Nova nota de churn:** substitua `data/churn_scores.csv` com as colunas `base`, `customerID`, `churn_probability`,
  `predicted_churn` e `risk_decile` (o modelo mínimo está em `contracts/churn_scores.template.csv`) e faça novo Deploy.
- **Nova leitura dos comentários:** rode o notebook 11, exporte com `contracts/export_feedback.sql` e substitua
  `data/feedback_classifications.csv`.

## Limites

- **A nota ordena, não é chance exata:** o modelo foi treinado com as classes balanceadas, o que infla a nota (no grupo
  de maior risco, a nota média fica perto de 0,9 e saem quase 8 em cada 10).
- **O comentário não tem data:** a pesquisa incluiu clientes ativos e já cancelados. A leitura descreve o relato, não o
  status atual; um relato de cancelamento pede conferência no cadastro.
- **Ações simuladas:** ofertas, descontos e agendamentos dependem de integração com os sistemas da empresa.

Arquitetura, contratos dos arquivos e o desenho de produção: [ARCHITECTURE.md](ARCHITECTURE.md). Validação: [VALIDACAO.md](VALIDACAO.md).
