
import os
import yt_dlp
from pydub import AudioSegment

from utils.deno_setup import ensure_deno

DOWNLOAD_DIR = "downloades"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_youtube_audio(url: str) -> str:
    """Download audio from a YouTube URL using yt-dlp and Deno."""

    deno_path = ensure_deno()

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(
            DOWNLOAD_DIR, "%(id)s.%(ext)s"
        ),
        "noplaylist": True,

        # Limit retries to avoid repeatedly requesting blocked videos
        "retries": 1,
        "extractor_retries": 1,
        "fragment_retries": 1,
        "socket_timeout": 20,

        # JavaScript challenge support
        "remote_components": ["ejs:npm"],
        "js_runtimes": {
            "deno": {"path": deno_path}
        },

        # YouTube player clients
        "extractor_args": {
            "youtube": {
                "player_client": ["tv", "web_safari"]
            }
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if not os.path.isfile(filename):
            raise FileNotFoundError(
                f"Downloaded audio file not found: {filename}"
            )

        return filename

    except yt_dlp.utils.DownloadError as e:
        error = str(e).lower()

        if "sign in to confirm" in error or "not a bot" in error:
            message = (
                "YouTube requires a bot verification check. "
                "The cloud server could not download this video. "
                "Try again later or upload the audio file."
            )
        elif "429" in error or "too many requests" in error:
            message = (
                "YouTube is rate-limiting the server. "
                "Wait before trying again."
            )
        elif "403" in error or "forbidden" in error:
            message = (
                "YouTube denied the download request. "
                "This may be a server-side access restriction. "
                "Try again later or upload the audio file."
            )
        else:
            message = f"YouTube download failed: {e}"

        raise RuntimeError(message) from e


def convert_to_wav(input_path: str) -> str:
    """Convert an audio file to mono, 16 kHz WAV."""

    if not os.path.isfile(input_path):
        raise FileNotFoundError(
            f"Input audio file not found: {input_path}"
        )

    output_path = (
        os.path.splitext(input_path)[0] + "_converted.wav"
    )

    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path, format="wav")

    return output_path


def chunk_audio(
    wav_path: str, chunk_minutes: int = 10
) -> list[str]:
    """Split WAV audio into chunks of the specified length."""

    if not os.path.isfile(wav_path):
        raise FileNotFoundError(
            f"WAV file not found: {wav_path}"
        )

    if chunk_minutes <= 0:
        raise ValueError("chunk_minutes must be greater than zero.")

    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000
    chunks = []

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start:start + chunk_ms]

        chunk_path = (
            f"{os.path.splitext(wav_path)[0]}_chunk_{i}.wav"
        )

        chunk.export(chunk_path, format="wav")
        chunks.append(chunk_path)

    return chunks


def process_input(source: str) -> list[str]:
    """Process a YouTube URL or local audio/video file."""

    if not source or not source.strip():
        raise ValueError("Please provide a YouTube URL or file path.")

    source = source.strip()

    if source.startswith(("http://", "https://")):
        print("Detected YouTube URL. Downloading audio...")
        audio_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        audio_path = source

    wav_path = convert_to_wav(audio_path)

    print("Preparing audio chunks...")
    chunks = chunk_audio(wav_path)

    print(f"Audio ready: {len(chunks)} chunk(s) created.")
    return chunks
