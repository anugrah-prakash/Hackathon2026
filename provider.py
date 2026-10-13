"""TrustedTokens configuration. Never fall back to OpenAI's API endpoint or key."""
import os
from dataclasses import dataclass

BASE_URL = 'https://api.trustedtokens.eu/v1'


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str
    vision_model: str

    @property
    def ready(self):
        return bool(self.api_key and self.api_key != 'your_trustedtokens_key_here' and self.model)


def settings(env=None):
    env = os.environ if env is None else env
    return Settings(
        api_key=env.get('TRUSTEDTOKENS_API_KEY', '').strip(),
        model=env.get('TRUSTEDTOKENS_MODEL', 'zai-org/GLM-5.3').strip(),
        vision_model=env.get('TRUSTEDTOKENS_VISION_MODEL', '').strip())


def make_client(config, factory=None):
    if not config.ready:
        raise ValueError('Set TRUSTEDTOKENS_API_KEY and TRUSTEDTOKENS_MODEL in .env.')
    if factory is None:
        from openai import OpenAI
        factory = OpenAI
    return factory(api_key=config.api_key, base_url=BASE_URL, timeout=120, max_retries=1)


def api_error_message(error):
    status = getattr(error, 'status_code', None)
    if status == 401:
        return 'TrustedTokens rejected the API key. Check TRUSTEDTOKENS_API_KEY in .env and restart.'
    if status == 403:
        return 'TrustedTokens denied access. Check your account and permissions for the selected model.'
    if status == 429:
        return 'TrustedTokens rate or quota limit reached. Check your account usage and retry later.'
    if status in (400, 404, 422):
        return ('TrustedTokens rejected the request or model. Check the model ID in your account. '
                'For photos/scans, use an image-capable TRUSTEDTOKENS_VISION_MODEL. '
                'The selected model must support structured output on the Responses API.')
    return 'Could not complete the TrustedTokens request. Check network access and service availability, then retry.'
