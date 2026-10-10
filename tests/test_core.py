import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from io import BytesIO
from PIL import Image
from core import Letter, Claim, Action, Audit, EvidenceError, analyze_candidate as analyze, validate, parse, ResponseFormatError
from pydantic import ValidationError
from documents import pages, MAX_BYTES

SOURCE = 'Bitte senden Sie den Nachweis innerhalb von zwei Wochen nach Zugang. Kontakt: Amt.'
QUOTE = 'Bitte senden Sie den Nachweis innerhalb von zwei Wochen nach Zugang.'


def example():
    return Letter(summary=Claim(explanation='The office requests proof.', quote=QUOTE),
                  actions=[Action(task=Claim(explanation='Send the proof.', quote=QUOTE),
                                  deadline='innerhalb von zwei Wochen nach Zugang', amount=None)],
                  consequences=[], contact_quote='Kontakt: Amt.', unclear_quotes=[])


class EvidenceTests(unittest.TestCase):
    def test_relative_deadline_preserved(self):
        self.assertEqual(validate(example(), SOURCE).actions[0].deadline,
                         'innerhalb von zwei Wochen nach Zugang')

    def test_invented_date(self):
        letter = example()
        letter.actions[0].deadline = '21.10.2026'
        with self.assertRaises(EvidenceError): validate(letter, SOURCE)

    def test_wrong_action_date(self):
        letter = example()
        letter.actions[0].deadline = '20.10.2026'
        with self.assertRaises(EvidenceError):
            validate(letter, SOURCE + ' Anderer Termin: 20.10.2026')

    def test_fabricated_quote(self):
        letter = example()
        letter.summary.quote = 'You owe money.'
        with self.assertRaises(EvidenceError): validate(letter, SOURCE)

    def test_numeric_addition(self):
        letter = example()
        letter.summary.explanation = 'Pay 900 euros.'
        with self.assertRaises(EvidenceError): validate(letter, SOURCE)

    def test_unreadable_evidence(self):
        letter = example()
        letter.summary.quote = '[unreadable]'
        with self.assertRaises(EvidenceError): validate(letter, SOURCE + ' [unreadable]')

    def test_unknowns_remain_unknown(self):
        letter = Letter(summary=None, actions=[], consequences=[], contact_quote=None, unclear_quotes=[])
        self.assertIsNone(validate(letter, SOURCE).summary)

    def test_audit_blocks_result(self):
        client = Mock()
        client.responses.parse.side_effect = [
            SimpleNamespace(status='completed', output_parsed=example()),
            SimpleNamespace(status='completed', output_parsed=Audit(supported_and_complete=False))]
        with self.assertRaises(EvidenceError): analyze(client, 'test', SOURCE)

    def test_audit_reason_reaches_user_error(self):
        client = Mock()
        client.responses.parse.side_effect = [
            SimpleNamespace(status='completed', output_parsed=example()),
            SimpleNamespace(status='completed', output_parsed=Audit(
                supported_and_complete=False, reason='The task omits a condition.'))]
        with self.assertRaisesRegex(EvidenceError, 'The task omits a condition'):
            analyze(client, 'test', SOURCE)

    def test_success_requires_audit(self):
        client = Mock()
        client.responses.parse.side_effect = [
            SimpleNamespace(status='completed', output_parsed=example()),
            SimpleNamespace(status='completed', output_parsed=Audit(supported_and_complete=True))]
        self.assertEqual(analyze(client, 'test', SOURCE), example())
        self.assertEqual(client.responses.parse.call_count, 2)
        self.assertFalse(client.responses.parse.call_args.kwargs['store'])

    def test_refusal_or_truncation(self):
        client = Mock()
        client.responses.parse.return_value = SimpleNamespace(status='incomplete', output_parsed=None)
        with self.assertRaises(EvidenceError): analyze(client, 'test', SOURCE)

    def test_input_limits(self):
        for text in ('', ' ' , 'x' * 50001):
            with self.assertRaises(EvidenceError): analyze(Mock(), 'test', text)


class FormatTests(unittest.TestCase):
    def broken(self):
        try:
            Letter.model_validate_json('{"summary":')
        except ValidationError as error:
            return error

    def test_malformed_json_retries_then_recovers(self):
        client = Mock()
        client.responses.parse.side_effect = [self.broken(),
            SimpleNamespace(status='completed', output_parsed=example())]
        self.assertEqual(parse(client, 'test', Letter, 'rules', SOURCE), example())
        self.assertEqual(client.responses.parse.call_count, 2)

    def test_repeated_malformed_json_is_safe(self):
        client = Mock()
        client.responses.parse.side_effect = self.broken()
        with self.assertRaises(ResponseFormatError) as caught:
            parse(client, 'test', Letter, 'rules', SOURCE)
        self.assertNotIn('summary', str(caught.exception))
        self.assertEqual(client.responses.parse.call_count, 2)

    def test_incomplete_partial_result_is_discarded(self):
        client = Mock()
        client.responses.parse.return_value = SimpleNamespace(status='incomplete', output_parsed=example())
        with self.assertRaises(ResponseFormatError):
            parse(client, 'test', Letter, 'rules', SOURCE)
        self.assertEqual(client.responses.parse.call_count, 2)

    def test_refusal_not_retried(self):
        client = Mock()
        client.responses.parse.return_value = SimpleNamespace(status='completed', output_parsed=None)
        with self.assertRaises(ResponseFormatError):
            parse(client, 'test', Letter, 'rules', SOURCE)
        self.assertEqual(client.responses.parse.call_count, 1)


class DocumentTests(unittest.TestCase):
    def test_image(self):
        data = BytesIO()
        Image.new('RGB', (100, 100), 'white').save(data, 'JPEG')
        self.assertTrue(pages(data.getvalue())[0].startswith(b'\x89PNG'))

    def test_pdf_page_limit(self):
        import fitz
        with fitz.open() as doc:
            for _ in range(7): doc.new_page()
            with self.assertRaises(ValueError): pages(doc.tobytes())

    def test_bad_file(self):
        with self.assertRaises(Exception): pages(b'not an image')

    def test_size_limit(self):
        with self.assertRaises(ValueError): pages(b'x' * (MAX_BYTES + 1))


if __name__ == '__main__':
    unittest.main()


class PartialAnswerTests(unittest.TestCase):
    def test_one_failed_question_preserves_other_answers(self):
        from unittest.mock import patch
        from core import analyze as whole
        with patch('core.analyze_candidate', side_effect=[example(), EvidenceError('Unclear date'), example()]):
            result = whole(Mock(), 'test', SOURCE)
        self.assertIsNotNone(result.summary)
        self.assertEqual(result.actions, [])
        self.assertEqual(len(result.notices), 1)
        self.assertIn('Question 2', result.notices[0])

    def test_all_failures_are_explicit(self):
        from unittest.mock import patch
        from core import analyze as whole
        with patch('core.analyze_candidate', side_effect=ResponseFormatError('Invalid response')):
            result = whole(Mock(), 'test', SOURCE)
        self.assertIsNone(result.summary)
        self.assertEqual(len(result.notices), 3)

    def test_all_questions_supported(self):
        from unittest.mock import patch
        from core import analyze as whole
        with patch('core.analyze_candidate', return_value=example()) as call:
            result = whole(Mock(), 'test', SOURCE)
        self.assertEqual(call.call_count, 3)
        self.assertEqual(result.actions, example().actions)
        self.assertEqual(result.notices, [])
