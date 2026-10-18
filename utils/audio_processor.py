
import yt_dlp
from pydub import AudioSegment
import os

DOWNLOAD_DIR = "downloades"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_youtube_audio(url: str) -> str:
    output_path = os.path.join(
        DOWNLOAD_DIR, "%(title)s.%(ext)s"
    )
ydl_opts = {
    "format": "best/bestvideo+bestaudio",
    "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
    "noplaylist": True,
    "quiet": False,
    "retries": 3,
    "extractor_retries": 3,
    "remote_components": ["ejs:npm"],
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
        }
    ],
}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        wav_path = os.path.splitext(filename)[0] + ".wav"

    if not os.path.exists(wav_path):
        raise FileNotFoundError(
            f"Converted WAV file not found: {wav_path}"
        )

    return wav_path


def convert_to_wav(input_path: str) -> str:
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"

    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path, format="wav")

    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
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


def process_input(source: str) -> list:
    if source.startswith(("http://", "https://")):
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Preparing audio chunks...")
    chunks = chunk_audio(wav_path)

    print(f"Audio ready: {len(chunks)} chunk(s) created.")

    return chunks
