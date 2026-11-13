-- Execute somente apos criar/revisar a view do notebook AI_QUERY v2.
-- Exporte o resultado como CSV: feedback_classifications.csv.
-- Envie o arquivo para data/ e redeploy. Nao e executado pelo app.
SELECT base, customerID, situacao_relatada, sentimento,
       to_json(motivos) AS motivos,
       evidencia_situacao, resumo, status_processamento,
       prompt_version, CAST(processado_em AS STRING) AS processado_em
FROM workspace.default.feedback_clientes_v2;
