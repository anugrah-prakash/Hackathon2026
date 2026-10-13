"""List available TrustedTokens models without sending any letter data."""
from pathlib import Path
from dotenv import load_dotenv
from openai import APIError
from provider import make_client, settings, api_error_message

if __name__ == '__main__':
    load_dotenv(Path(__file__).with_name('.env'))
    try:
        for model in make_client(settings()).models.list():
            data = model.model_dump()
            print(model.id, data.get('architecture', {}))
    except APIError as error:
        raise SystemExit(api_error_message(error)) from None
    except ValueError as error:
        raise SystemExit(str(error)) from None
