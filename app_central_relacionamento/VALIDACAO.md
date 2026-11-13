# Validação (12/11/2026)

| Conferência | Resultado |
|---|---|
| Testes automáticos (`python -m unittest discover -s tests -v`) | 10 passando |
| Clientes carregados | 5.634 do histórico e 1.409 da inferência; 100 comentários com quebra de linha lidos sem virar linhas extras |
| Notas de churn | 7.043, uma por cliente, todas entre 0 e 1; iguais às dos arquivos do modelo (`abt_completa_scored.csv` e `inferencia_scored.csv`), sem recálculo |
| Previsão e decil | Todos os `Churn_Previsto` são 0 ou 1 e os decis estão entre D1 e D10; na inferência, 562 com 1 e 847 com 0 |
| Leitura dos comentários | 7.043 clientes, sem ID faltante, repetido ou desconhecido; 5.432 válidos e 1.611 com alerta (inferência: 1.077 e 332). Textos conferidos com a origem, normalizando só espaços e quebras de linha |
| Filtros | Combinados no servidor antes da paginação; faixas inválidas devolvem erro 422 |
| API | `/health`, `/api/summary`, `/api/customers` e o perfil devolvem 200; ID inexistente devolve 404 |
| Jornada | As cinco missões contam uma vez; erro no quiz não conclui a missão; o progresso não guarda dados de clientes |

Origem e hashes dos arquivos: `data/manifest.json` e `data/score_manifest.json`.
