
import re
from urllib.parse import urlparse, parse_qs

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


def is_youtube_url(source: str) -> bool:
    return (
        "youtube.com" in urlparse(source).netloc.lower()
        or "youtu.be" in urlparse(source).netloc.lower()
    )


def get_video_id(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if host.endswith("youtu.be"):
        video_id = parsed.path.strip("/").split("/")[0]
    elif host.endswith("youtube.com"):
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        else:
            match = re.match(
                r"^/(?:shorts|embed|live)/([^/?]+)",
                parsed.path,
            )
            video_id = match.group(1) if match else ""
    else:
        video_id = ""

    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("Please provide a valid YouTube video URL.")

    return video_id


def get_youtube_captions(
    source: str, language: str = "english"
) -> str:
    """Retrieve available YouTube captions as plain text."""

    from youtube_transcript_api import YouTubeTranscriptApi

    video_id = get_video_id(source)

    if language.lower() == "hinglish":
        languages = ["hi", "en"]
    else:
        languages = ["en", "hi"]

    captions = YouTubeTranscriptApi().fetch(
        video_id,
        languages=languages,
    )

    transcript = " ".join(
        snippet.text for snippet in captions
    ).strip()

    if not transcript:
        raise RuntimeError("The available captions are empty.")

    return transcript


def run_pipeline(source: str, language: str = "english") -> dict:
    print("🚀 Starting AI Video Assistant")

    transcript = None

    # First try the existing audio + Whisper pipeline.
    try:
        chunks = process_input(source)
        transcript = transcribe_all(chunks, language)

    except Exception as audio_error:
        print(f"⚠️ Audio processing failed: {audio_error}")

        # Only YouTube URLs can use the captions fallback.
        if not is_youtube_url(source):
            raise RuntimeError(
                f"Could not process the input file: {audio_error}"
            ) from audio_error

        print("📝 Trying the YouTube captions fallback...")

        try:
            transcript = get_youtube_captions(source, language)
            print("✅ Transcript retrieved from captions.")

        except Exception as caption_error:
            raise RuntimeError(
                "Audio download failed and captions could not be "
                "retrieved. The video may have no available captions, "
                "or YouTube may be blocking the request. "
                "Please upload an audio/video file instead. "
                f"Audio error: {audio_error}. "
                f"Caption error: {caption_error}"
            ) from caption_error

    if not transcript or not transcript.strip():
        raise RuntimeError("No transcript was generated.")

    print(
        f"Raw transcription (first 300 characters): "
        f"{transcript[:300]}"
    )

    title = generate_title(transcript)
    summary = summarize(transcript)
    action_items = extract_action_items(transcript)
    decisions = extract_key_decisions(transcript)
    questions = extract_questions(transcript)

    print("🔎 Building RAG chain...")
    rag_chain = build_rag_chain(transcript)

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
    }


if __name__ == "__main__":
    source = input(
        "Enter YouTube URL or local file path: "
    ).strip()

    language = (
        input("Language (english/hinglish): ").strip()
        or "english"
    )

    try:
        result = run_pipeline(source, language)

        print("\n" + "=" * 60)
        print(f"📌 Title: {result['title']}")
        print(f"\n📋 Summary:\n{result['summary']}")
        print(f"\n✅ Action Items:\n{result['action_items']}")
        print(f"\n🔑 Key Decisions:\n{result['key_decisions']}")
        print(f"\n❓ Open Questions:\n{result['open_questions']}")
        print("=" * 60)

        print("\n💬 Chat with your video (type 'exit' to quit)\n")
        rag_chain = result["rag_chain"]

        while True:
            question = input("You 👤: ").strip()

            if question.lower() in ("exit", "quit", "q"):
                print("👋 Goodbye!")
                break

            if not question:
                continue

            try:
                answer = ask_question(rag_chain, question)
                print(f"\n🤖 Assistant: {answer}\n")
            except Exception as e:
                print(f"❌ Error answering question: {e}")

    except Exception as e:
        print(f"\n❌ Could not process this video: {e}")
