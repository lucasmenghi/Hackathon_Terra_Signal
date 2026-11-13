"""Leitura de snapshots CSV. Sem Spark, token pessoal ou chamada de IA no app."""
import csv
import json
import math
from pathlib import Path

BASES = ('inference', 'history')
SITUATIONS = {'CANCELAMENTO_RELATADO', 'TROCA_RELATADA', 'DECISAO_SAIDA',
              'CONSIDERA_SAIDA', 'INTENCAO_PERMANENCIA', 'SEM_DECLARACAO', 'AMBIGUO'}
SENTIMENTS = {'POSITIVO', 'NEGATIVO', 'MISTO', 'NEUTRO', 'INDETERMINADO'}
MOTIVES = {'PRECO', 'CONEXAO', 'SUPORTE', 'COBRANCA', 'CONCORRENCIA', 'PRODUTOS', 'OUTROS',
           'PRECO_CONCORRENCIA', 'PAGAMENTO', 'TECNICO', 'PESSOAL', 'PRODUTO_COBERTURA', 'ATENDIMENTO'}


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream, strict=True)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError(f'Cabeçalho inválido: {path.name}')
        for line, row in enumerate(reader, 2):
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f'CSV desalinhado: {path.name}, registro {line}')
            yield row


def number(value):
    try:
        result = float(str(value).strip())
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None


def boolean(value):
    val = str(value).strip().lower()
    return True if val == 'yes' else False if val in {'no', 'no internet service', 'no phone service'} else None


def nullable(value):
    """Exports do SQL podem representar NULL como texto literal."""
    if value is None or str(value).strip().lower() in {'', 'null'}:
        return None
    return str(value).strip()


def recommendation(customer):
    """Regras de demonstração. Não determina elegibilidade nem efeito causal."""
    nlp = customer['nlp']
    if nlp['status'] != 'DISPONIVEL':
        return {'title': 'Confirme a necessidade atual', 'text':
            'Consulte os produtos e pergunte qual é a necessidade de hoje. A pesquisa não tem data individual; '
            'confirme se o relato ainda se aplica. Score e interpretação do texto não são presumidos.',
            'source': 'Orientação fixa de demonstração; sem LLM conectada'}
    situation, motives = nlp['situation'], set(nlp['motives'])
    if situation in {'CANCELAMENTO_RELATADO', 'TROCA_RELATADA'}:
        title, text = 'Confira o status cadastral', 'A pesquisa relata saída já realizada. Confirme o status atual antes de oferecer retenção preventiva ou recuperação.'
    elif situation == 'AMBIGUO':
        title, text = 'Esclareça o relato', 'Há ambiguidade no comentário. Confirme com o cliente sua situação e a necessidade atual.'
    elif motives & {'CONEXAO', 'SUPORTE', 'TECNICO'}:
        title, text = 'Investigue o problema técnico', 'Confirme se o problema persiste e faça o diagnóstico com o cliente. Avalie encaminhamento técnico conforme as regras disponíveis.'
    elif motives & {'PRECO', 'CONCORRENCIA', 'PRECO_CONCORRENCIA', 'PAGAMENTO'}:
        title, text = 'Entenda o orçamento e as condições', 'Confirme a dificuldade relatada. Consulte somente alternativas elegíveis, sem prometer desconto ou condições não aprovadas.'
    else:
        title, text = 'Aprofunde a conversa', 'Confirme os motivos relatados na pesquisa e identifique a necessidade atual antes de propor uma ação.'
    return {'title': title, 'text': text, 'source': 'Regra determinística demonstrativa; não é recomendação de uma LLM'}


class Repository:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.records = {}
        self.counts = {}
        for base in BASES:
            count = 0
            for raw in read_csv(self.directory / f'{base}.csv'):
                if not {'customerID', 'CustomerFeedback', 'InternetService', 'MonthlyCharges', 'tenure'} <= raw.keys():
                    raise ValueError(f'Colunas obrigatórias ausentes em {base}.csv')
                key = (base, raw['customerID'].strip())
                if not key[1] or key in self.records:
                    raise ValueError(f'ID ausente ou duplicado em {base}')
                self.records[key] = self._customer(base, raw)
                count += 1
            if not count:
                raise ValueError(f'Base vazia: {base}')
            self.counts[base] = count
        self.attach_scores()
        self.attach_nlp()
        for customer in self.records.values():
            customer['recommendation'] = recommendation(customer)

    def _customer(self, base, raw):
        tenure = number(raw.get('tenure'))
        return {'id': raw['customerID'].strip(), 'base': base, 'name': None, 'phone': None,
                'tenure': tenure, 'monthly': number(raw.get('MonthlyCharges')),
                'total_charges': number(raw.get('TotalCharges')),
                'income': number(raw.get('MonthlyIncome')),
                'internet': raw.get('InternetService'), 'contract': raw.get('Contract'),
                'payment': raw.get('PaymentMethod'), 'feedback': raw.get('CustomerFeedback', ''),
                'historical_churn': raw.get('Churn') if base == 'history' else None,
                'products': {k: boolean(raw.get(k)) for k in
                    ['PhoneService', 'StreamingTV', 'StreamingMovies', 'OnlineSecurity',
                     'OnlineBackup', 'DeviceProtection', 'TechSupport']},
                'score': {'status': 'PENDENTE', 'probability': None, 'model_version': None, 'scored_at': None},
                'nlp': {'status': 'PENDENTE' if raw.get('CustomerFeedback', '').strip() else 'SEM_FEEDBACK',
                        'situation': None, 'sentiment': None, 'motives': [], 'evidence': None,
                        'summary': None, 'processed_at': None, 'prompt_version': None,
                        'source_status': None, 'imported': False, 'routing': None},
                'quality_notes': [k for k in ['tenure', 'MonthlyCharges', 'TotalCharges', 'MonthlyIncome']
                                  if number(raw.get(k)) is None]}

    def _optional_rows(self, name):
        path = self.directory / name
        if not path.exists():
            return []
        rows = list(read_csv(path))
        seen = set()
        for row in rows:
            if not {'base', 'customerID'} <= row.keys():
                raise ValueError(f'{name}: exigidos base e customerID')
            key = (row['base'].strip(), row['customerID'].strip())
            if key not in self.records or key in seen:
                raise ValueError(f'{name}: chave inexistente ou duplicada {key}')
            seen.add(key)
        return rows

    def attach_scores(self):
        for row in self._optional_rows('churn_scores.csv'):
            key = (row['base'].strip(), row['customerID'].strip())
            val = number(row.get('churn_probability'))
            if val is None or not 0 <= val <= 1:
                raise ValueError(f'churn_scores.csv: probabilidade inválida para {key}')
            self.records[key]['score'] = {'status': 'DISPONIVEL', 'probability': val,
                'probability_raw': row['churn_probability'],
                'model_version': row.get('model_version') or None, 'scored_at': row.get('scored_at') or None,
                'predicted_churn': nullable(row.get('predicted_churn')),
                'modeling_split': nullable(row.get('modeling_split')),
                'risk_decile': nullable(row.get('risk_decile'))}

    def attach_nlp(self):
        for row in self._optional_rows('feedback_classifications.csv'):
            key = (row['base'].strip(), row['customerID'].strip())
            situation = nullable(row.get('situacao_relatada'))
            sentiment = nullable(row.get('sentimento'))
            try:
                motives = json.loads(nullable(row.get('motivos')) or '[]')
            except json.JSONDecodeError as exc:
                raise ValueError(f'Lista de motivos JSON inválida: {key}') from exc
            if not isinstance(motives, list) or any(not isinstance(x, str) or x not in MOTIVES for x in motives):
                raise ValueError(f'Motivos inválidos: {key}')
            source_feedback = nullable(row.get('feedback_original'))
            if source_feedback and ' '.join(source_feedback.split()) != ' '.join(self.records[key]['feedback'].split()):
                raise ValueError(f'Feedback classificado difere do texto de origem: {key}')
            source_status = nullable(row.get('status_processamento'))
            error_statuses = {'ERRO_API', 'RESPOSTA_NULA', 'NAO_PROCESSADO', 'SEM_FEEDBACK'}
            status = 'DISPONIVEL' if situation in SITUATIONS and sentiment in SENTIMENTS else 'REVISAR'
            if source_status and source_status != 'VALIDO_TECNICAMENTE':
                status = 'REVISAR'
            if source_status in error_statuses:
                status = source_status
            self.records[key]['nlp'] = {'status': status, 'situation': situation or None,
                'sentiment': sentiment or None, 'motives': motives,
                'evidence': nullable(row.get('evidencia_situacao')), 'summary': nullable(row.get('resumo')),
                'processed_at': nullable(row.get('processado_em')),
                'prompt_version': nullable(row.get('prompt_version')), 'source_status': source_status,
                'imported': True, 'routing': nullable(row.get('encaminhamento_sugerido'))}

    def get(self, base, customer_id):
        return self.records.get((base, customer_id))

    def list(self, base='inference', query='', sentiment='', risk_only=False, offset=0, limit=20, portfolio='all', decile='', predicted_churn='', min_probability=None, max_probability=None):
        rows = [c for (b, _), c in self.records.items() if b == base
                and (portfolio == 'all' or (base == 'history' and c['historical_churn'] == ('No' if portfolio == 'retention' else 'Yes')))
                and query.casefold() in c['id'].casefold()
                and (not sentiment or c['nlp']['sentiment'] == sentiment)
                and (not decile or c['score'].get('risk_decile') == decile)
                and (not predicted_churn or c['score'].get('predicted_churn') == predicted_churn)
                and (min_probability is None or (c['score']['probability'] is not None and c['score']['probability'] >= min_probability))
                and (max_probability is None or (c['score']['probability'] is not None and c['score']['probability'] <= max_probability))
                and (not risk_only or (c['score']['probability'] is not None and c['score']['probability'] >= .6))]
        rows.sort(key=lambda c: (c['score']['probability'] is None,
                                -(c['score']['probability'] or 0), c['id']))
        items = [{'id': c['id'], 'base': c['base'], 'score': c['score'],
                  'sentiment': c['nlp']['sentiment'], 'nlp_status': c['nlp']['status'],
                  'situation': c['nlp']['situation'], 'motives': c['nlp']['motives'],
                  'internet': c['internet'], 'contract': c['contract']} for c in rows[offset:offset+limit]]
        return {'items': items, 'total': len(rows), 'offset': offset, 'limit': limit}

    def summary(self, base, portfolio='all'):
        rows = [c for (b, _), c in self.records.items() if b == base
                and (portfolio == 'all' or (base == 'history' and c['historical_churn'] == ('No' if portfolio == 'retention' else 'Yes')))]
        return {'base': base, 'customers': len(rows),
                'scored': sum(c['score']['status'] == 'DISPONIVEL' for c in rows),
                'high_risk': sum(c['score']['probability'] is not None and c['score']['probability'] >= .6 for c in rows),
                'classified': sum(c['nlp']['status'] == 'DISPONIVEL' for c in rows),
                'nlp_imported': sum(c['nlp']['imported'] for c in rows),
                'nlp_alerts': sum(c['nlp']['imported'] and c['nlp']['status'] != 'DISPONIVEL' for c in rows),
                'negative': sum(c['nlp']['status'] == 'DISPONIVEL' and c['nlp']['sentiment'] == 'NEGATIVO' for c in rows),
                'mode': 'SNAPSHOT_REAL_ACOES_SIMULADAS', 'counts': self.counts,
                'currency': 'BRL', 'feedback_date': None}
