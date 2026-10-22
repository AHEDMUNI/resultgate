import unittest
from pathlib import Path
from resultgate.browseract_demo import CSVInput, normalize_csv
import json
ROOT=Path(__file__).resolve().parents[1]
class CSVTests(unittest.TestCase):
    def payload(self,text=None):
        return CSVInput(csv_text=text if text is not None else (ROOT/'examples/browseract/accepted/result.csv').read_text(),expected_urls=json.loads((ROOT/'examples/browseract/reference/report.json').read_text())['expected_urls'])
    def test_actual_export_preserved_and_valid(self):
        p=self.payload(); result=normalize_csv(p)
        self.assertTrue(result['validation']['all_successful'])
        self.assertEqual(20,result['validation']['received_unique'])
        self.assertEqual('£51.77',result['raw_rows'][0]['price'])
        row=result['normalized_report']['rows'][0]
        self.assertEqual('51.77',row['price']); self.assertEqual('£',row['currency']); self.assertIsNone(row['currency_iso'])
        self.assertEqual('2026-10-22T00:39:41Z',row['checked_at'])
        self.assertFalse(result['validation']['execution_independently_verified'])
    def test_missing_and_duplicate_rows_fail(self):
        p=self.payload(); lines=p.csv_text.splitlines(True)
        self.assertFalse(normalize_csv(self.payload(''.join(lines[:-1])))['validation']['complete'])
        self.assertFalse(normalize_csv(self.payload(''.join(lines[:-1]+[lines[1]])))['validation']['complete'])
    def test_bad_headers_and_columns(self):
        p=self.payload()
        for text in (p.csv_text.replace('product_name','price',1),p.csv_text.replace('£51.77','51,77',1)):
            with self.assertRaises(ValueError): normalize_csv(self.payload(text))
    def test_ambiguous_value_retains_original(self):
        result=normalize_csv(self.payload(self.payload().csv_text.replace('£51.77','£1,234',1).replace(',£1,234,',',"£1,234",',1)))
        self.assertFalse(result['validation']['all_successful']); self.assertEqual('£1,234',result['raw_rows'][0]['price'])
    def test_missing_timestamp_not_invented(self):
        result=normalize_csv(self.payload(self.payload().csv_text.replace('2026-10-22T00:39:41Z','',1)))
        self.assertFalse(result['validation']['complete']);self.assertIsNone(result['normalized_report']['rows'][0]['checked_at'])
