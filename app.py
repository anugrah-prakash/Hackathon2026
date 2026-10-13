"""Run with: streamlit run app.py"""
import hashlib
import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from openai import APIError
from provider import settings, make_client, api_error_message
from core import transcribe, EvidenceError, ResponseFormatError
from pipeline import analyze
from documents import pages, embedded_text
from formatting import deadline_label
from visuals import apply_theme, hero, journey, empty_state, processing, results_banner

load_dotenv(Path(__file__).with_name('.env'))
st.set_page_config(page_title='Decoding the Amt', page_icon='✉️', layout='centered')
apply_theme()
hero()
journey()
if st.button('Clear letter and start again'):
    for key in list(st.session_state):
        del st.session_state[key]
    st.session_state['generation'] = os.urandom(8).hex()
    st.rerun()
generation = st.session_state.get('generation', 'initial')
mode = st.radio('Add your letter', ['Upload file', 'Take a picture'], horizontal=True)
if mode == 'Upload file':
    upload = st.file_uploader('PDF, JPG, PNG or WebP · up to 20 MB · PDF up to 6 pages',
                              type=['pdf', 'jpg', 'jpeg', 'png', 'webp'], key='upload_' + generation)
else:
    st.caption('For a letter with multiple pages, upload one PDF containing all pages.')
    upload = st.camera_input('Photograph the full page in good light', key='camera_' + generation)
if upload is None:
    empty_state()
    st.stop()
raw = upload.getvalue()
identity = hashlib.sha256(raw).hexdigest()
if identity != st.session_state.get('identity'):
    for key in ('text', 'answer', 'answer_source', 'reviewed', 'consent'):
        st.session_state.pop(key, None)
    st.session_state.identity = identity
try:
    images = pages(raw)
except Exception:
    st.error('Cannot open this file. Use an unlocked PDF (1–6 pages) or a clear JPG/PNG/WebP under 20 MB.')
    st.stop()
with st.expander('View the original letter', expanded=False):
    for i, img in enumerate(images, 1):
        st.image(img, caption=f'Page {i}')
st.caption('Analysis sends your letter to the TrustedTokens API. This app keeps it in session memory, '
           'does not write letters to disk, and requests store=False. Provider retention policies still apply.')
consent = st.checkbox('I agree to send this letter to the TrustedTokens API.', key='consent')
config = settings()
ready = config.ready
if not ready:
    st.info('Add TRUSTEDTOKENS_API_KEY to .env, check TRUSTEDTOKENS_MODEL, then restart the app.')
model = config.model


def client():
    return make_client(config)


if st.button('1 · Read the letter', disabled=not (ready and consent), type='primary'):
    for name in ('text', 'answer', 'answer_source', 'reviewed'):
        st.session_state.pop(name, None)
    activity = processing()
    try:
        with st.spinner('Reading the original wording…'):
            text_layer = embedded_text(raw)
            if text_layer is not None:
                st.session_state.text = text_layer
            elif config.vision_model:
                st.session_state.text = transcribe(client(), config.vision_model, images)
            else:
                raise EvidenceError('This file needs image transcription. Set TRUSTEDTOKENS_VISION_MODEL '
                                    'to an image-capable model ID from your TrustedTokens account, then restart. '
                                    'PDFs with usable embedded text do not need a vision model.')
    except ResponseFormatError as error:
        st.error(str(error))
    except APIError as error:
        st.error(api_error_message(error))
    except EvidenceError as error:
        st.error(str(error))
    finally:
        activity.empty()
if 'text' not in st.session_state:
    st.stop()
st.subheader('Check the transcription')
st.write('Compare this text with the original, especially dates and amounts. Correct any reading errors. '
         'Keep [unreadable] where you cannot confirm the wording.')
def reset_review():
    st.session_state.reviewed = False
    st.session_state.pop('answer', None)


source = st.text_area('Letter text', height=300, key='text', max_chars=50000, on_change=reset_review)
reviewed = st.checkbox('I checked the text against all pages of the letter.', key='reviewed')
if source != st.session_state.get('answer_source'):
    st.session_state.pop('answer', None)
if st.button('2 · Explain my next steps', type='primary', disabled=not (ready and consent and reviewed and source.strip())):
    st.session_state.pop('answer', None)
    activity = processing()
    try:
        with st.spinner('Extracting next steps and checking their evidence…'):
            st.session_state.answer = analyze(client(), model, source)
            st.session_state.answer_source = source
    except ResponseFormatError as error:
        st.error(str(error))
    except EvidenceError as error:
        st.warning('The draft answer did not pass an evidence check. This does not necessarily '
                   'mean your letter is unreadable.')
        st.write('Why the answer was withheld:')
        st.text(str(error))
        st.info('Compare the transcription with every original page, especially dates and amounts. '
                'If the text is correct, you can try Explain my next steps again: the AI may have '
                'made an extraction error. Every attempt must pass the same checks. '
                'If the letter itself is unclear, ask the sender to clarify. '
                'Do not change the transcription merely to make the check pass.')
    except APIError as error:
        st.error(api_error_message(error))
    finally:
        activity.empty()
answer = st.session_state.get('answer')
if answer is None:
    st.stop()


def claim(c):
    st.write(c.explanation)
    with st.expander('Show supporting wording'):
        st.text(c.quote)


st.divider()
results_banner()
if answer.notices:
    st.warning('Some answers could not be verified. The supported answers are shown below; this may be incomplete.')
    with st.expander('See which answers need clarification'):
        for notice in answer.notices:
            st.text(notice)
st.subheader('1. What is this letter about, in one sentence?')
if answer.summary:
    claim(answer.summary)
else:
    st.warning('The subject could not be established from the letter.')
st.subheader('2. What do I have to do, and by when?')
if not answer.actions:
    st.info('No clear action was extracted. This does not confirm that nothing is required; ask the sender if unsure.')
for i, action in enumerate(answer.actions, 1):
    with st.container(border=True):
        st.markdown(f'**Action {i}**')
        claim(action.task)
        st.write(deadline_label(action.deadline))
        if action.deadline:
            st.caption('Deadline as written in the letter')
            st.text(action.deadline)
        st.write('Amount — exact wording:')
        st.text(action.amount or 'No clear amount attached to this action was extracted.')
st.caption('Only deadlines stated in the letter are shown.')
st.subheader("3. What happens if I don't?")
if answer.consequences:
    for c in answer.consequences:
        claim(c)
else:
    st.info('No explicit consequence was extracted from this letter. That does not mean there are no consequences; ask the sender.')
if answer.unclear_quotes or '[unreadable]' in source.lower():
    st.warning('Some wording is unclear. Do not rely on an inferred deadline or amount. Ask the sender to clarify.')
    for q in answer.unclear_quotes:
        st.text(q)
st.subheader('Who can clarify?')
if answer.contact_quote:
    st.write('The letter identifies this sender or contact:')
    st.text(answer.contact_quote)
else:
    st.write('Ask the sender using contact details on the original letter. If you cannot identify the office, '
             'ask your university international office or a migration advice service for help.')
st.write('Ask: “What exactly must I do, by what deadline, and what happens if I cannot comply?”')
st.caption('AI transcription and interpretation can still be wrong. Evidence checks reduce errors but cannot guarantee accuracy. '
           'Check the original before acting; this is a reading aid, not legal advice.')
st.download_button('Download explanation (JSON)', answer.model_dump_json(indent=2),
                   file_name='letter_explanation.json', mime='application/json')
