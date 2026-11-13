# Arquitetura e limites

## Versão entregue

```text
history.csv + inference.csv  [snapshot incluído no source]
churn_scores.csv            [opcional, resultado real do modelo]
feedback_classifications.csv [opcional, resultado real AI_QUERY]
       ↓ validação no startup
Repository → FastAPI → interface HTML/CSS/JS
                         ↓
               ações apenas simuladas
```

O app lê os dados no início e os mantém em memória. Listagens são paginadas no servidor, com consulta individual para o texto completo. A ausência dos arquivos opcionais não impede o app de funcionar. Não se tenta inferir sentimentos ou scores a partir de palavras ou do rótulo Churn.

As bases são separadas por `base` e `customerID`. O histórico não é tratado como carteira ativa: a interface mostra só a inferência. O alvo original pode ser consultado na seção de auditoria do perfil histórico, explicitamente como rótulo retrospectivo, sem determinar status atual. Uma falha de numérico no dado bruto gera ausência no campo formatado e aviso de qualidade; não se refaz o dataprep do grupo no app.

## Integração em produção — desenho proposto, não implementado

```text
Silvers/Gold → job de pontuação de churn → tabela de scores versionada
Feedback    → job AI_QUERY + revisão    → tabela de interpretação
Cadastro atual + elegibilidade         → serviço operacional
                    ↓
          camada de leitura por customerID
                    ↓
   FastAPI + regras elegíveis + LLM opcional
                    ↓
       operador confirma ação → sistema transacional + auditoria
```

Para substituir CSVs por Unity Catalog, implemente outro adaptador de leitura mantendo o contrato das rotas. Use identidade do app e autenticação gerenciada; atribua `CAN USE` ao SQL Warehouse, `USE CATALOG`, `USE SCHEMA` e `SELECT` apenas às tabelas necessárias. Não embuta PAT no source. Avalie autenticação por usuário quando a autorização precisar refletir permissões individuais. Cache, refresh, paginação e limites devem ser definidos nesse adaptador.

Scores e NLP devem ser calculados em jobs fora do atendimento, com versão e origem. Antes de exibir scores como risco futuro, são necessários data de referência, horizonte de churn e validação temporal. Hoje essas referências não existem: a avaliação é retrospectiva.

Um serviço de recomendação real deve receber fatos validados, políticas e ações elegíveis. A LLM não autoriza descontos, não altera cadastro e não inventa ofertas. Qualquer escrita deve exigir autorização, confirmação do operador, idempotência e registro de auditoria. As ações atuais não oferecem esse serviço e não gravam informações.

## Regras de apresentação

- A fila usa a nota recebida, em ordem decrescente. Previsão e decil vêm do arquivo do modelo, sem novo limiar no app.
- Sem classificação, o sentimento fica pendente. Comentário não é “último feedback recente”: só existe uma resposta de pesquisa por cliente, sem data individual.
- Declaração de permanência não zera risco.
- Relato de cancelamento pede conferência cadastral, não confirmação automática de status.
- “Produtos e relacionamento” não é share of wallet, porque não temos gasto total do cliente com fornecedores.
- Não há nomes ou telefones nos CSVs: nenhum é inventado.
- Dados ficam nas respostas da API e no source privado; revisores com acesso ao app conseguem consultar os clientes. Restringir as permissões do app é parte necessária da implantação.
- Logs não registram texto do feedback. A API retorna `no-store`; os assets não carregam bibliotecas externas.

## Contratos NLP

Situações: `CANCELAMENTO_RELATADO`, `TROCA_RELATADA`, `DECISAO_SAIDA`, `CONSIDERA_SAIDA`, `INTENCAO_PERMANENCIA`, `SEM_DECLARACAO`, `AMBIGUO`.

Sentimentos: `POSITIVO`, `NEGATIVO`, `MISTO`, `NEUTRO`, `INDETERMINADO`.

Motivos do SQL v2: `PRECO`, `CONEXAO`, `SUPORTE`, `COBRANCA`, `CONCORRENCIA`, `PRODUTOS`, `OUTROS`.

Códigos adicionais aceitos na importação, de uma classificação manual anterior: `PRECO_CONCORRENCIA`, `PAGAMENTO`, `TECNICO`, `PESSOAL`, `PRODUTO_COBERTURA`, `ATENDIMENTO`. Aceitar o código não reclassifica textos. Produto/cobertura representa querer um serviço que a empresa não oferecia.
