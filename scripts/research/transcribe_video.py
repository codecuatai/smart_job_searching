import os
import sys
import time
import soundfile as sf
from faster_whisper import WhisperModel

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def format_timestamp(seconds: float) -> str:
    millis = int((seconds - int(seconds)) * 1000)
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def main():
    wav_path = "audio_16k.wav"
    output_srt = "subtitles.srt"
    
    print(f"Loading audio from {wav_path}...")
    audio, sr = sf.read(wav_path, dtype="float32")
    duration_secs = len(audio) / sr
    print(f"Loaded {len(audio)} samples ({duration_secs:.2f}s, ~{duration_secs/60:.2f} mins)")
    
    # Using 'base' model for high speed & good accuracy
    print("Loading faster-whisper 'base' model on CPU (int8)...")
    t0 = time.time()
    model = WhisperModel("base", device="cpu", compute_type="int8")
    print(f"Model loaded in {time.time() - t0:.2f}s")
    
    print("Transcribing audio (language='vi')...")
    t1 = time.time()
    segments, info = model.transcribe(
        audio,
        language="vi",
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )
    
    srt_lines = []
    count = 1
    
    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue
        start_ts = format_timestamp(segment.start)
        end_ts = format_timestamp(segment.end)
        srt_lines.append(f"{count}\n{start_ts} --> {end_ts}\n{text}\n")
        print(f"[{start_ts} -> {end_ts}] {text}")
        count += 1
        
    with open(output_srt, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines) + "\n")
        
    print(f"\nDone! Transcribed {count - 1} segments in {time.time() - t1:.2f}s")
    print(f"Saved to {output_srt}")

if __name__ == "__main__":
    main()
