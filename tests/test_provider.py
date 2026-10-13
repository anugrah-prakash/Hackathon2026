import unittest
from unittest.mock import Mock
from provider import settings, make_client, BASE_URL, api_error_message


class ProviderTests(unittest.TestCase):
    def test_routes_key_and_model_to_trustedtokens(self):
        config=settings({'TRUSTEDTOKENS_API_KEY':'test-key','TRUSTEDTOKENS_MODEL':'custom/model'})
        factory=Mock()
        make_client(config,factory)
        self.assertEqual(factory.call_args.kwargs['base_url'],BASE_URL)
        self.assertEqual(factory.call_args.kwargs['api_key'],'test-key')
        self.assertEqual(config.model,'custom/model')

    def test_does_not_use_openai_credentials(self):
        self.assertFalse(settings({'OPENAI_API_KEY':'old-secret'}).ready)

    def test_placeholder_rejected(self):
        with self.assertRaises(ValueError):
            make_client(settings({'TRUSTEDTOKENS_API_KEY':'your_trustedtokens_key_here'}),Mock())

    def test_separate_vision_model(self):
        self.assertEqual(settings({'TRUSTEDTOKENS_VISION_MODEL':'vision/id'}).vision_model,'vision/id')
        self.assertEqual(settings({}).vision_model,'')

    def test_errors_do_not_echo_private_payload(self):
        error=Mock(status_code=401)
        self.assertIn('rejected the API key',api_error_message(error))
