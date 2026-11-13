import csv
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from repository import Repository


class RepositoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository(ROOT / 'data')

    def test_real_counts_and_received_probabilities(self):
        self.assertEqual(self.repo.counts, {'inference': 1409, 'history': 5634})
        for c in self.repo.records.values():
            self.assertIsNotNone(c['score']['probability'])
            self.assertGreaterEqual(c['score']['probability'], 0)
            self.assertLessEqual(c['score']['probability'], 1)
            self.assertIsNone(c['name'])
            self.assertIsNone(c['phone'])

    def test_original_multiline_feedback_not_split_into_customers(self):
        count = sum('\n' in c['feedback'] for c in self.repo.records.values())
        self.assertEqual(count, 100)

    def test_search_pagination_and_filter(self):
        first = self.repo.list(limit=10)
        second = self.repo.list(offset=10, limit=10)
        self.assertEqual(first['total'], 1409)
        self.assertFalse(set(c['id'] for c in first['items']) & set(c['id'] for c in second['items']))
        self.assertEqual(self.repo.list(risk_only=True)['total'],
                         sum(c['score']['probability'] >= .6 for (b, _), c in self.repo.records.items() if b == 'inference'))
        self.assertGreater(self.repo.list(sentiment='NEGATIVO')['total'], 0)
        self.assertEqual(self.repo.list(query=first['items'][0]['id'])['total'], 1)

    def test_uploaded_feedback_coverage_and_nulls(self):
        historical = self.repo.summary('history')
        self.assertEqual(historical['nlp_imported'], 5634)
        self.assertEqual(historical['classified'], 4355)
        self.assertEqual(historical['nlp_alerts'], 1279)
        inference = self.repo.summary('inference')
        self.assertEqual(inference['nlp_imported'], 1409)
        self.assertEqual(inference['classified'], 1077)
        self.assertEqual(inference['nlp_alerts'], 332)
        for c in self.repo.records.values():
            self.assertNotEqual(c['nlp']['sentiment'], 'null')
            self.assertNotEqual(c['nlp']['situation'], 'null')
            self.assertNotEqual(c['nlp']['evidence'], 'null')
            if c['nlp']['status'] == 'REVISAR':
                self.assertIn('sem LLM', c['recommendation']['source'])

    def test_active_portfolios_are_disjoint_and_complete(self):
        retention = self.repo.summary('history', 'retention')
        recovery = self.repo.summary('history', 'recovery')
        self.assertEqual(retention['customers'], 4130)
        self.assertEqual(recovery['customers'], 1504)
        self.assertEqual(retention['customers'] + recovery['customers'], 5634)
        for portfolio, expected in [('retention', 'No'), ('recovery', 'Yes')]:
            page = self.repo.list('history', limit=100, portfolio=portfolio)
            self.assertEqual(page['total'], retention['customers'] if portfolio == 'retention' else recovery['customers'])
            for row in page['items']:
                self.assertEqual(self.repo.get('history', row['id'])['historical_churn'], expected)

    def test_decile_filter_before_pagination_and_with_sentiment(self):
        for portfolio in ['retention', 'recovery']:
            counts = []
            for i in range(1, 11):
                page = self.repo.list('history', portfolio=portfolio, decile=f'D{i}', limit=100)
                counts.append(page['total'])
                self.assertTrue(all(c['score']['risk_decile'] == f'D{i}' for c in page['items']))
            self.assertEqual(sum(counts), self.repo.summary('history', portfolio)['customers'])
        page = self.repo.list('history', portfolio='retention', decile='D1', sentiment='NEGATIVO')
        self.assertTrue(all(c['score']['risk_decile']=='D1' and c['sentiment']=='NEGATIVO' for c in page['items']))

    def test_inference_prediction_and_probability_filters(self):
        self.assertEqual(self.repo.list('inference')['total'], 1409)
        self.assertEqual(self.repo.list('inference', predicted_churn='1')['total'], 562)
        self.assertEqual(self.repo.list('inference', predicted_churn='0')['total'], 847)
        filtered = self.repo.list('inference', predicted_churn='1', decile='D1',
                                  min_probability=.85, max_probability=.95, limit=100)
        expected = [c for (base, _), c in self.repo.records.items() if base=='inference'
                    and c['score']['predicted_churn']=='1' and c['score']['risk_decile']=='D1'
                    and .85 <= c['score']['probability'] <= .95]
        self.assertEqual(filtered['total'], len(expected))
        self.assertTrue(all(c['base']=='inference' and .85 <= c['score']['probability'] <= .95
                            for c in filtered['items']))
        self.assertEqual(self.repo.list('inference', min_probability=0, max_probability=0)['total'], 0)

    def test_routing_comes_from_received_file(self):
        with (ROOT/'data/feedback_classifications.csv').open(encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.DictReader(stream))
        for row in rows[:20]:
            customer = self.repo.get(row['base'], row['customerID'])
            self.assertEqual(customer['nlp']['routing'], row['encaminhamento_sugerido'])

    def test_scores_match_import_and_order_descending(self):
        with (ROOT/'data/churn_scores.csv').open(encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 7043)
        for row in rows:
            score = self.repo.get(row['base'], row['customerID'])['score']
            self.assertEqual(score['probability'],
                             float(row['churn_probability']))
            self.assertEqual(score['probability_raw'], row['churn_probability'])
            self.assertEqual(score['predicted_churn'], row['predicted_churn'])
            self.assertEqual(score['risk_decile'], row['risk_decile'])
            self.assertIn(score['predicted_churn'], {'0', '1'})
            self.assertIn(score['risk_decile'], {f'D{i}' for i in range(1, 11)})
        for base, scope in [('inference','all'), ('history','retention'), ('history','recovery')]:
            page = self.repo.list(base, limit=100, portfolio=scope)
            probabilities = [r['score']['probability'] for r in page['items']]
            self.assertEqual(probabilities, sorted(probabilities, reverse=True))

    def test_enrichment_and_invalid_scores(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            for name in ('history.csv', 'inference.csv'):
                shutil.copy2(ROOT / 'data' / name, path / name)
            key = next(k for k in self.repo.records if k[0] == 'inference')
            with (path/'churn_scores.csv').open('w', newline='', encoding='utf-8') as f:
                w = csv.writer(f);w.writerow(['base','customerID','churn_probability']);w.writerow([*key,.82])
            with (path/'feedback_classifications.csv').open('w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(['base','customerID','situacao_relatada','sentimento','motivos','status_processamento'])
                w.writerow([*key,'CANCELAMENTO_RELATADO','MISTO',json.dumps(['PRECO']),'VALIDO_TECNICAMENTE'])
            enriched = Repository(path)
            self.assertEqual(enriched.get(*key)['score']['probability'], .82)
            self.assertEqual(enriched.get(*key)['nlp']['status'], 'DISPONIVEL')
            self.assertEqual(enriched.get(*key)['recommendation']['title'], 'Confira o status cadastral')
            self.assertEqual(enriched.list()['items'][0]['id'], key[1])
            with (path/'churn_scores.csv').open('w', newline='', encoding='utf-8') as f:
                w = csv.writer(f);w.writerow(['base','customerID','churn_probability']);w.writerow([*key,'NaN'])
            with self.assertRaises(ValueError):
                Repository(path)


if __name__ == '__main__':
    unittest.main()
