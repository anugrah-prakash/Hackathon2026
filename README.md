# Decoding the Amt — TrustedTokens edition

## Run

Use Python 3.11+. Extract this project, open a terminal in its folder, and run:

```sh
python -m venv .venv
```

Activate on Windows: `.venv\Scripts\Activate.ps1`

Activate on macOS/Linux: `source .venv/bin/activate`

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Before launching, configure `.env` as shown below. When updating, migrate your key to the new
TRUSTEDTOKENS_API_KEY name; old OPENAI_API_KEY settings are deliberately ignored. Stop the old process with Ctrl+C before restarting.

## Current pipeline

1. Read a PDF's usable text layer, or transcribe images/scans using vision.
2. Let the reader compare and correct the text against the original.
3. Number source lines and extract all three answers together using `pipeline.py`.
4. Ask a second model request to correct the draft and add omitted explicit facts.
5. Build evidence quotes from the cited source lines locally. Reject invalid citations,
   unsupported numbers, and deadlines/amounts absent from the action's evidence.
6. Show concise answers, with source excerpts inside expandable panels.

This replaces the old Boolean-review/per-question pipeline. `core.py` retains legacy
helpers for regression tests, but the app now imports `pipeline.analyze`.
No answer for the supplied sample is hard-coded into the application. The sample
text and expected responses are used only in offline tests.

If one item fails evidence matching, other supported items remain, with a warning.
A wholly empty result is now an extraction error, never a claim that the letter has
no requirements. Malformed structured responses are discarded and retried once.
Scanned inputs normally use three model calls; PDFs with usable text use two.
Retries can double those calls. API usage is billed to your API account.

The app accepts a single PDF (1–6 pages), image or camera photo up to 20 MB.
For multi-page photos combine them into one PDF. Browser camera access requires
permission and localhost or HTTPS. Theme, SVG graphics and animations run locally.
Reduced-motion settings are respected.

## Limits and privacy

AI interpretation can still be wrong. Source citations and a corrective review do
not prove semantic accuracy. Verify the original before acting. This is a reading
aid, not a legal decision system. Relative dates are not calculated. The model must
not infer missing deadlines, amounts or penalties. Missing facts should prompt asking
the sender. No outside legal knowledge is injected into the interpretation.

Letter data is sent to TrustedTokens after consent. Requests use store=False; provider
retention rules still apply. The app keeps session data in memory without intentionally
writing letter files or logging their text. Clearing the app is not secure memory
erasure or deletion of provider records. Keep .env private. Public deployment requires
authentication, HTTPS, cost controls and a privacy/security review.

## Verification

```sh
python -m unittest discover -s tests -v
```

37 offline tests pass, including legacy regressions and the new line-cited pipeline.
Tests of model behavior use mocked responses: they do not establish live AI accuracy.
The supplied Finanzamt PDF's native text extraction was tested directly. Live API and
browser testing were not possible in the build environment.

For the supplied sample, expected content is: the office wants the 2025 tax return;
submit online via ELSTER by 31 October 2026; if you believe filing is unnecessary,
explain why in writing. Lateness may lead to a late fee, tax estimation and a threat
of a coercive fine. The original letter specifies no penalty amount.

## TrustedTokens setup

The provider's documented base URL is `https://api.trustedtokens.eu/v1`.
The app uses its documented OpenAI-compatible Responses endpoint and structured
outputs. The `openai` Python package remains a client library; no OpenAI API key
is required and requests are explicitly routed to TrustedTokens.

Edit `.env`:

```dotenv
TRUSTEDTOKENS_API_KEY=your_actual_trustedtokens_key
TRUSTEDTOKENS_MODEL=zai-org/GLM-5.3
TRUSTEDTOKENS_VISION_MODEL=
```

The text model above is the example ID in the provider's documentation; select a
model available to your account that supports structured output. To inspect IDs:

```sh
python list_models.py
```

For camera photos, image uploads and scanned PDFs, set TRUSTEDTOKENS_VISION_MODEL
to an image-capable model ID from that catalog. The model-listing command prints
architecture metadata when the provider supplies it. Do not assume the text model
supports vision. If no vision model is configured, the app explains that requirement
instead of sending images to an unsuitable text model. PDFs with usable text on
every page do not need a vision model. API request compatibility does not imply
that every hosted model supports every modality or structured output option.

The included .env contains placeholders only. Never send your key in chat, commit it,
or include your completed .env in a shared archive. Restart the app after editing it.
Authentication and request errors now give provider-specific guidance without echoing
private request bodies or keys. Provider retention policies still apply to store=False.

Tests verify endpoint/key routing, configuration, and existing extraction behavior.
There has been no live TrustedTokens request or account-specific model test.

Provider documentation: https://trustedtokens.eu/docs/
Model catalog: https://trustedtokens.eu/models/
