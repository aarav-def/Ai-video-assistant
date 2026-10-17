"""
AI VIDEO ASSISTANT - dark, mobile-style Streamlit UI.
Run with:  streamlit run app.py
Place next to your existing `core/` and `utils/` folders and `.env`.
"""
import html
import os
import re
import tempfile

import streamlit as st
from dotenv import load_dotenv

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()

st.set_page_config(
    page_title="AI VIDEO ASSISTANT",
    page_icon="🎬",
    layout="centered",
)

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    color-scheme: dark;
    --bg: #090e1d;
    --card: #121a30;
    --card-2: #182039;
    --line: #242d4a;
    --text: #eef1fb;
    --muted: #8e99b8;
    --violet: #8b5cf6;
    --violet-soft: #c4b5fd;
    --cyan: #22d3ee;
    --green: #34d399;
}

html, body, [class*="css"], .stMarkdown, button, input, textarea {
    font-family: 'Inter', sans-serif;
}
.stApp { background: var(--bg); color: var(--text); }
.stApp p, .stApp label, .stApp span, .stApp li { color: var(--text); }
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 760px; padding-top: 1.4rem; padding-bottom: 4rem; }

/* Header */
.brand { display: flex; align-items: center; gap: 0.7rem; margin-bottom: 1.1rem; }
.brand-logo {
    width: 40px; height: 40px; border-radius: 12px;
    background: #1b2347; border: 1px solid var(--line);
    display: flex; align-items: center; justify-content: center;
}
.brand-name { font-weight: 800; font-size: 1.2rem; letter-spacing: 0.01em; }

.pill {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: rgba(139, 92, 246, 0.25); color: var(--violet-soft);
    border: 1px solid rgba(139, 92, 246, 0.5);
    border-radius: 999px; padding: 0.22rem 0.75rem;
    font-size: 0.78rem; font-weight: 600; margin-bottom: 0.8rem;
}
.hero-title { font-size: 2.3rem; font-weight: 800; line-height: 1.1; letter-spacing: -0.03em; margin: 0 0 0.6rem 0; }
.hero-sub { color: var(--muted); font-size: 1.02rem; line-height: 1.5; margin: 0 0 1.4rem 0; }

/* Cards (bordered containers) */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--card);
    border: 1px solid var(--line) !important;
    border-radius: 18px;
}

/* Inputs */
div[data-baseweb="input"], div[data-baseweb="select"] > div, div[data-baseweb="base-input"] {
    background: var(--card-2) !important;
    border-color: var(--line) !important;
    border-radius: 12px !important;
}
.stTextInput input, .stSelectbox div { color: var(--text) !important; }
[data-testid="stFileUploader"] section { background: var(--card-2); border: 1px dashed var(--line); border-radius: 12px; }
.stRadio label p { color: var(--text) !important; }

/* Buttons */
.stButton > button, .stDownloadButton > button {
    background: var(--card-2); color: var(--text);
    border: 1px solid var(--line); border-radius: 12px; font-weight: 600;
}
.stButton > button:hover, .stDownloadButton > button:hover { border-color: var(--violet); color: #fff; }
.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #7c6cf6, #cdbcff);
    color: #141432; border: none; font-weight: 700; font-size: 1.05rem;
    padding: 0.75rem 1rem; box-shadow: 0 8px 30px rgba(124, 108, 246, 0.35);
}
.stButton > button[kind="primary"]:hover { filter: brightness(1.07); color: #141432; }
.stButton > button[kind="primary"]:disabled { opacity: 0.45; box-shadow: none; }

/* Top navigation + intelligence tabs */
.stTabs [data-baseweb="tab-list"] { gap: 0.5rem; border-bottom: none; flex-wrap: wrap; }
.stTabs [data-baseweb="tab"] {
    background: var(--card-2); border: 1px solid var(--line);
    border-radius: 999px; padding: 0.35rem 1rem; height: auto;
    color: var(--muted); font-weight: 600; font-size: 0.9rem;
}
.stTabs [aria-selected="true"] {
    background: rgba(139, 92, 246, 0.3); color: #fff; border-color: var(--violet);
}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

/* Result card */
.result { display: flex; gap: 1rem; align-items: center; }
.thumb {
    width: 150px; min-width: 150px; height: 90px; border-radius: 12px;
    background: #1b2347 center/cover no-repeat; border: 1px solid var(--line);
}
.ready { color: var(--cyan); font-size: 0.78rem; font-weight: 700; letter-spacing: 0.04em; }
.r-title { font-size: 1.1rem; font-weight: 700; line-height: 1.25; margin: 0.2rem 0 0.35rem 0; }
.r-meta { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: var(--muted); }
.r-meta b { color: var(--violet-soft); font-weight: 500; }

/* Section headings inside cards */
.sec-title { font-size: 1.25rem; font-weight: 700; margin: 0 0 0.6rem 0; }
.muted { color: var(--muted); font-size: 0.85rem; }

/* Transcript feed */
.utt {
    background: var(--card-2); border: 1px solid var(--line);
    border-left: 3px solid var(--violet);
    border-radius: 14px; padding: 0.9rem 1rem; margin-bottom: 0.8rem;
}
.utt-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem; }
.utt-tag {
    background: rgba(34, 211, 238, 0.12); color: var(--cyan);
    border-radius: 6px; padding: 0.1rem 0.5rem; font-size: 0.78rem; font-weight: 600;
}
.utt-words { font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: var(--muted); }
.utt-text { font-size: 1.02rem; line-height: 1.55; }
mark { background: rgba(250, 204, 21, 0.3); color: #fff; border-radius: 3px; padding: 0 2px; }

/* Empty state steps */
.step { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 1rem 1.1rem; margin-bottom: 0.7rem; }
.step b { display: block; margin-bottom: 0.15rem; }
.step span { color: var(--muted); font-size: 0.92rem; }

@media (max-width: 560px) {
    .hero-title { font-size: 1.9rem; }
    .result { flex-direction: column; align-items: flex-start; }
    .thumb { width: 100%; height: 150px; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

LOGO_SVG = """
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#8b9bff" stroke-width="2.4" stroke-linecap="round">
  <path d="M4 10v4M8 6v12M12 3v18M16 8v8M20 11v2"/>
</svg>
"""

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
st.session_state.setdefault("result", None)
st.session_state.setdefault("meta", {})
st.session_state.setdefault("messages", [])
st.session_state.setdefault("history", [])
st.session_state.setdefault("show_all", False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def youtube_id(url: str):
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([\w-]{11})", url or "")
    return m.group(1) if m else None


def save_upload(uploaded_file) -> str:
    suffix = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        return tmp.name


def to_segments(transcript: str, sentences_per_segment: int = 3) -> list[str]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?।])\s+", transcript) if s.strip()]
    return [
        " ".join(sentences[i : i + sentences_per_segment])
        for i in range(0, len(sentences), sentences_per_segment)
    ]


def highlight(text: str, query: str) -> str:
    safe = html.escape(text)
    if not query:
        return safe
    pattern = re.compile(re.escape(html.escape(query)), re.IGNORECASE)
    return pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", safe)


def count_items(text) -> int:
    lines = str(text).splitlines()
    return sum(1 for ln in lines if re.match(r"^\s*([-*•]|\d+[.)])\s+", ln))


def tab_label(name: str, text) -> str:
    n = count_items(text)
    return f"{name} ({n})" if n else name


def run_pipeline_ui(source: str, language: str) -> dict:
    with st.status("Working on your video…", expanded=True) as status:
        st.write("Fetching and splitting the audio")
        chunks = process_input(source)
        st.write("Transcribing speech")
        transcript = transcribe_all(chunks, language)
        st.write("Writing the title and summary")
        title = generate_title(transcript)
        summary = summarize(transcript)
        st.write("Finding action items, decisions and open questions")
        action_items = extract_action_items(transcript)
        decisions = extract_key_decisions(transcript)
        questions = extract_questions(transcript)
        st.write("Preparing the chat")
        rag_chain = build_rag_chain(transcript)
        status.update(label="Your video is ready", state="complete", expanded=False)
    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
    }


def ask(question: str) -> None:
    st.session_state.messages.append({"role": "user", "content": question})
    try:
        reply = ask_question(st.session_state.result["rag_chain"], question)
    except Exception as e:
        reply = f"I couldn't answer that: {e}"
    st.session_state.messages.append({"role": "assistant", "content": reply})


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    f'<div class="brand"><div class="brand-logo">{LOGO_SVG}</div>'
    '<div class="brand-name">AI VIDEO ASSISTANT</div></div>',
    unsafe_allow_html=True,
)

tab_main, tab_chat, tab_history = st.tabs(["🎙️ Transcribe", "💬 Chat", "🕘 History"])

# ===========================================================================
# TRANSCRIBE
# ===========================================================================
with tab_main:
    st.markdown(
        '<div class="pill">✨ Transcript, summary and chat in one place</div>'
        '<h1 class="hero-title">YouTube video to text</h1>'
        '<p class="hero-sub">Turn any YouTube link or recording into a transcript, '
        "action items, key decisions and open questions. Then ask it anything.</p>",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        input_type = st.radio("Video source", ["YouTube link", "Upload a file"], horizontal=True)
        source = None
        label = ""
        if input_type == "YouTube link":
            url = st.text_input(
                "YouTube URL",
                placeholder="https://www.youtube.com/watch?v=…",
                label_visibility="collapsed",
            )
            source = url.strip() or None
            label = source or ""
        else:
            up = st.file_uploader(
                "Video or audio file",
                type=["mp4", "mkv", "mov", "avi", "webm", "mp3", "wav", "m4a"],
                label_visibility="collapsed",
            )
            if up is not None:
                source, label = up, up.name

        language = st.selectbox("Spoken language", ["english", "hinglish"])
        go = st.button("⚡ Analyze video", type="primary", use_container_width=True, disabled=source is None)

    if go and source is not None:
        try:
            path = save_upload(source) if input_type == "Upload a file" else source
            res = run_pipeline_ui(path, language)
            meta = {
                "label": label,
                "language": language,
                "thumb": f"https://img.youtube.com/vi/{youtube_id(label)}/hqdefault.jpg"
                if input_type == "YouTube link" and youtube_id(label)
                else None,
            }
            st.session_state.result = res
            st.session_state.meta = meta
            st.session_state.messages = []
            st.session_state.show_all = False
            st.session_state.history.insert(0, {"result": res, "meta": meta})
        except Exception as e:
            st.session_state.result = None
            st.error(f"Could not process this video: {e}")

    result = st.session_state.result
    meta = st.session_state.meta

    if result is None:
        st.write("")
        for head, body in [
            ("1. Add a video", "Paste a YouTube link or upload a file above."),
            ("2. Read the highlights", "Summary, action items, decisions and open questions."),
            ("3. Ask follow-ups", "Use the Chat tab to question the transcript."),
        ]:
            st.markdown(f'<div class="step"><b>{head}</b><span>{body}</span></div>', unsafe_allow_html=True)
    else:
        words = len(result["transcript"].split())

        # Result card
        thumb_style = f"background-image:url('{meta['thumb']}')" if meta.get("thumb") else ""
        with st.container(border=True):
            st.markdown(
                f"""
                <div class="result">
                    <div class="thumb" style="{thumb_style}"></div>
                    <div>
                        <div class="ready">● READY</div>
                        <div class="r-title">{html.escape(result['title'])}</div>
                        <div class="r-meta"><b>{words:,}</b> words &nbsp;•&nbsp; {html.escape(meta.get('language', '').title())}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Smart intelligence
        st.markdown('<div class="sec-title" style="margin-top:1.2rem">🧠 Smart intelligence</div>', unsafe_allow_html=True)
        t_sum, t_act, t_dec, t_q = st.tabs(
            [
                "Summary",
                tab_label("Action items", result["action_items"]),
                tab_label("Key decisions", result["key_decisions"]),
                tab_label("Open questions", result["open_questions"]),
            ]
        )
        with t_sum:
            with st.container(border=True):
                st.markdown(result["summary"])
        with t_act:
            with st.container(border=True):
                st.markdown(result["action_items"])
        with t_dec:
            with st.container(border=True):
                st.markdown(result["key_decisions"])
        with t_q:
            with st.container(border=True):
                st.markdown(result["open_questions"])

        # Transcript feed
        st.write("")
        with st.container(border=True):
            h1, h2 = st.columns([3, 2])
            h1.markdown('<div class="sec-title">📝 Transcript feed</div>', unsafe_allow_html=True)
            h2.download_button(
                "⬇ Download TXT",
                data=result["transcript"],
                file_name="transcript.txt",
                mime="text/plain",
                use_container_width=True,
            )

            query = st.text_input(
                "Filter",
                placeholder="🔍 Filter the transcript by keyword",
                label_visibility="collapsed",
            ).strip()

            segments = to_segments(result["transcript"])
            if query:
                matches = [(i, s) for i, s in enumerate(segments, 1) if query.lower() in s.lower()]
            else:
                matches = list(enumerate(segments, 1))

            limit = len(matches) if (st.session_state.show_all or query) else 3
            for idx, seg in matches[:limit]:
                st.markdown(
                    f"""
                    <div class="utt">
                        <div class="utt-head">
                            <span class="utt-tag">Segment {idx}</span>
                            <span class="utt-words">{len(seg.split())} words</span>
                        </div>
                        <div class="utt-text">{highlight(seg, query)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if not matches:
                st.markdown('<div class="muted">No segments match that keyword.</div>', unsafe_allow_html=True)
            else:
                f1, f2 = st.columns([3, 2])
                f1.markdown(
                    f'<div class="muted">Showing {min(limit, len(matches))} of {len(matches)} segments</div>',
                    unsafe_allow_html=True,
                )
                if not query and not st.session_state.show_all and len(matches) > 3:
                    if f2.button("Load full transcript ↓", use_container_width=True):
                        st.session_state.show_all = True
                        st.rerun()

# ===========================================================================
# CHAT
# ===========================================================================
with tab_chat:
    if st.session_state.result is None:
        st.info("Analyze a video first, then come back here to ask questions about it.")
    else:
        st.markdown(
            f'<div class="muted">Chatting about: {html.escape(st.session_state.result["title"])}</div>',
            unsafe_allow_html=True,
        )
        if not st.session_state.messages:
            st.write("")
            for text in [
                "What are the main points?",
                "What should I do after watching this?",
                "Who or what is mentioned most?",
            ]:
                if st.button(text, key=f"sugg_{text}", use_container_width=True):
                    with st.spinner("Thinking…"):
                        ask(text)
                    st.rerun()

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🎬"):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Ask something about this video"):
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(prompt)
            with st.chat_message("assistant", avatar="🎬"):
                with st.spinner("Thinking…"):
                    ask(prompt)
                st.markdown(st.session_state.messages[-1]["content"])

# ===========================================================================
# HISTORY
# ===========================================================================
with tab_history:
    if not st.session_state.history:
        st.info("Videos you analyze in this session will show up here.")
    else:
        st.markdown('<div class="muted">Kept for this browser session only.</div>', unsafe_allow_html=True)
        for i, item in enumerate(st.session_state.history):
            r, m = item["result"], item["meta"]
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"**{html.escape(r['title'])}**")
                c1.markdown(
                    f'<div class="muted">{len(r["transcript"].split()):,} words • '
                    f'{html.escape(m.get("language", "").title())}</div>',
                    unsafe_allow_html=True,
                )
                if c2.button("Open", key=f"open_{i}", use_container_width=True):
                    st.session_state.result = r
                    st.session_state.meta = m
                    st.session_state.messages = []
                    st.session_state.show_all = False
                    st.rerun()