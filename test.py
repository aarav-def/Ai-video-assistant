
from utils import audio_processor
from core.transcriber import transcribe_all

source = "https://youtu.be/YGgNBcIgI4s?si=NyH9qf6atmbHgctZ"

# Step 1: Download and split the audio
chunks = audio_processor.process_input(source)

# Step 2: Transcribe every chunk using Whisper
transcript = transcribe_all(chunks)

# Step 3: Display the complete text
print("\n" + "=" * 60)
print("YOUTUBE VIDEO TRANSCRIPTION")
print("=" * 60)
print(transcript)
print("=" * 60)

# Step 4: Save the text to a file
with open("transcription.txt", "w", encoding="utf-8") as file:
    file.write(transcript)

print("Transcript saved to transcription.txt")
