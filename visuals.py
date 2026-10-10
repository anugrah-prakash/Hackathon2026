"""Local SVG graphics and CSS animations; no CDN or external asset requests."""
from pathlib import Path
import streamlit as st


def apply_theme():
    st.markdown('<style>' + Path(__file__).with_name('styles.css').read_text() + '</style>',
                unsafe_allow_html=True)


def hero():
    # Static trusted markup only: never interpolate letter text into HTML.
    st.markdown('''<section class="amt-hero">
<div class="amt-intro"><div class="amt-eyebrow">DECODING THE AMT</div>
<h1>Official letter.<br><span>Clear next steps.</span></h1>
<p>A little clarity for your new life in Germany.<br>Understand your letter, one step at a time.</p>
<div class="amt-pill">Original wording beside every answer</div></div>
<div class="amt-art" aria-hidden="true"><svg viewBox="0 0 300 270" xmlns="http://www.w3.org/2000/svg">
<circle cx="153" cy="140" r="110" fill="#dedbff"/>
<circle cx="254" cy="51" r="9" fill="#f7bd69"/><circle cx="38" cy="192" r="7" fill="#53c5bb"/>
<g class="amt-letter"><rect x="73" y="36" width="156" height="192" rx="15" fill="#fff" stroke="#c8c2f4" stroke-width="2"/>
<rect x="95" y="61" width="46" height="8" rx="4" fill="#7160cf"/>
<path d="M95 91h108M95 109h91M95 127h101" stroke="#d5d2e6" stroke-width="7" stroke-linecap="round"/>
<rect x="93" y="149" width="113" height="52" rx="10" fill="#e3f5f0"/>
<path d="m106 173 7 7 14-16" fill="none" stroke="#087f73" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M140 169h50M140 181h37" stroke="#7bbdb1" stroke-width="5" stroke-linecap="round"/></g>
<g class="amt-envelope"><rect x="163" y="188" width="100" height="66" rx="12" fill="#6650bf"/>
<path d="m170 199 43 29 43-29" fill="none" stroke="#e4ddff" stroke-width="3" stroke-linejoin="round"/></g>
<path d="M44 60v18m-9-9h18M258 132v14m-7-7h14" stroke="#9587dc" stroke-width="3" stroke-linecap="round"/>
</svg></div></section>''', unsafe_allow_html=True)


def journey():
    st.markdown('''<div class="amt-steps" aria-label="Three steps to understand your letter">
<div><span class="amt-step-number">01</span><strong>Add your letter</strong><small>Upload or take a photo</small></div>
<div><span class="amt-step-number">02</span><strong>Check the wording</strong><small>Review dates and amounts</small></div>
<div><span class="amt-step-number">03</span><strong>See your next steps</strong><small>With supporting excerpts</small></div>
</div>''', unsafe_allow_html=True)


def empty_state():
    st.markdown('''<div class="amt-empty"><div class="amt-empty-icon" aria-hidden="true">✉</div>
<strong>Your next step starts with one letter.</strong>
<p>Tax notice, residence appointment or health insurance request?<br>
Add all pages, with dates, amounts and sender details visible.</p></div>''', unsafe_allow_html=True)


def processing():
    slot = st.empty()
    slot.markdown('''<div class="amt-processing" role="status"><span class="amt-dots" aria-hidden="true">
<i></i><i></i><i></i></span> Working through the wording…</div>''', unsafe_allow_html=True)
    return slot


def results_banner():
    st.markdown('''<div class="amt-result-banner"><span aria-hidden="true">✦</span>
<div><strong>Your letter, explained</strong><small>Three questions. Supporting wording. A clearer next step.</small></div>
</div>''', unsafe_allow_html=True)
