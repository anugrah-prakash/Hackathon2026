"""Offline regression contract using the user's sample, not a live model accuracy test."""
import unittest
from pathlib import Path
from unittest.mock import Mock
from types import SimpleNamespace
from core import Claim, Action, Letter, Audit, analyze, normalize, validate
from formatting import deadline_label
from documents import embedded_text

TEXT = Path(__file__).with_name('sample_tax_letter.txt').read_text()
SOURCE = normalize(TEXT)


def quote(start, end):
    a = SOURCE.index(start)
    b = SOURCE.index(end, a) + len(end)
    return SOURCE[a:b]


class SampleLetterTests(unittest.TestCase):
    def test_expected_answers_pass_full_pipeline(self):
        summary = Letter(summary=Claim(explanation='The tax office wants your 2025 income tax return.',
            quote=quote('Aufforderung zur Abgabe', 'Einkommensteuererklärung 2025')),
            actions=[], consequences=[], contact_quote=None, unclear_quotes=[])
        actions = Letter(summary=None, actions=[
            Action(task=Claim(explanation='Submit the tax return online via ELSTER.',
                quote=quote('Ich fordere Sie', 'übermitteln.')), deadline='31.10.2026', amount=None),
            Action(task=Claim(explanation='If you believe you do not have to file, write to the tax office and explain why.',
                quote=quote('Sofern Sie', 'schriftlich mit.')), deadline=None, amount=None)],
            consequences=[], contact_quote=None, unclear_quotes=[])
        consequences=Letter(summary=None, actions=[], consequences=[Claim(
            explanation='If you miss the deadline, the office may charge a late fee, estimate your tax assessment basis, and threaten a coercive fine.',
            quote=quote('Sollten Sie', 'anzudrohen.'))], contact_quote=None, unclear_quotes=[])
        client=Mock()
        responses=[]
        for part in (summary, actions, consequences):
            validate(part, TEXT)
            responses += [SimpleNamespace(status='completed',output_parsed=part),
                          SimpleNamespace(status='completed',output_parsed=Audit(supported_and_complete=True,reason=''))]
        client.responses.parse.side_effect=responses
        result=analyze(client,'test',TEXT)
        self.assertIn('2025',result.summary.explanation)
        self.assertEqual(len(result.actions),2)
        self.assertEqual(deadline_label(result.actions[0].deadline),'By 31 October 2026')
        self.assertIn('coercive',result.consequences[0].explanation)
        self.assertFalse(result.notices)

    def test_relative_dates_not_calculated(self):
        self.assertEqual(deadline_label('innerhalb von zwei Wochen'),'innerhalb von zwei Wochen')

    def test_invalid_date_not_repaired(self):
        self.assertEqual(deadline_label('31.02.2026'),'31.02.2026')

    def test_pdf_text_and_scanned_page_fallback(self):
        import fitz
        with fitz.open() as d:
            p=d.new_page()
            p.insert_text((30,40),'A clear text layer. ' * 8)
            self.assertIn('clear text layer',embedded_text(d.tobytes()))
            d.new_page()
            self.assertIsNone(embedded_text(d.tobytes()))
