"""Actual sample text, controlled model outputs; no claim of live model accuracy."""
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from pipeline import Draft, CitedClaim, CitedAction, materialize, source_lines, analyze
from core import EvidenceError
from formatting import deadline_label

TEXT = Path(__file__).with_name('sample_tax_letter.txt').read_text()


def ids(start, end):
    lines = source_lines(TEXT)
    a = next(i for i,s in enumerate(lines,1) if start in s)
    b = next(i for i,s in enumerate(lines,1) if i >= a and end in s)
    return list(range(a,b+1))


def candidate():
    return Draft(summary=CitedClaim(explanation='The tax office wants your 2025 tax return.',
        line_ids=ids('Aufforderung','2025')), actions=[
        CitedAction(task=CitedClaim(explanation='Submit the tax return online via ELSTER.',
            line_ids=ids('Ich fordere','übermitteln.')),deadline='31.10.2026',amount=None),
        CitedAction(task=CitedClaim(explanation='If you think you do not need to file, write to the tax office and explain why.',
            line_ids=ids('Sofern Sie','schriftlich mit.')),deadline=None,amount=None)],
        consequences=[CitedClaim(explanation='If you are late, you may pay a late fee; the office may estimate your tax and threaten a coercive fine.',
            line_ids=ids('Sollten Sie','anzudrohen.'))], contact_line_ids=[],unclear_line_ids=[])


class PipelineTests(unittest.TestCase):
    def test_sample_entire_pipeline(self):
        client=Mock()
        client.responses.parse.return_value=SimpleNamespace(status='completed',output_parsed=candidate())
        result=analyze(client,'test',TEXT)
        self.assertEqual(client.responses.parse.call_count,2)
        self.assertIn('2025',result.summary.explanation)
        self.assertEqual(deadline_label(result.actions[0].deadline),'By 31 October 2026')
        self.assertIn('ELSTER',result.actions[0].task.explanation)
        self.assertIn('explain why',result.actions[1].task.explanation)
        self.assertTrue(result.consequences)
        self.assertFalse(result.notices)

    def test_invalid_citation_does_not_erase_other_answers(self):
        c=candidate(); c.summary.line_ids=[999]
        result=materialize(c,TEXT)
        self.assertIsNone(result.summary)
        self.assertEqual(len(result.actions),2)
        self.assertTrue(result.notices)

    def test_invented_deadline_rejected(self):
        c=candidate(); c.actions[0].deadline='30.11.2026'
        result=materialize(c,TEXT)
        self.assertEqual(len(result.actions),1)
        self.assertTrue(result.notices)

    def test_empty_response_is_error_not_blank_answers(self):
        c=Draft(summary=None,actions=[],consequences=[],contact_line_ids=[],unclear_line_ids=[])
        with self.assertRaisesRegex(EvidenceError,'extraction failure'):
            materialize(c,TEXT)

    def test_reviewer_can_recover_empty_draft(self):
        empty=Draft(summary=None,actions=[],consequences=[],contact_line_ids=[],unclear_line_ids=[])
        client=Mock()
        client.responses.parse.side_effect=[SimpleNamespace(status='completed',output_parsed=empty),
                                          SimpleNamespace(status='completed',output_parsed=candidate())]
        self.assertIsNotNone(analyze(client,'test',TEXT).summary)
