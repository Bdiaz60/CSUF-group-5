# captioner.py
# AI Closed Captioning (batch/offline) module
# Usage: call functions from your app or run as script.

import os
import subprocess
import tempfile
import math
from datetime import timedelta
from pydub import AudioSegment

# Use google.genai in the feed module; re-use here
from google import genai

# Create Gemini client (expects GEMINI_API_KEY in env)
client = genai.Client()

# -------------------------
# Utility helpers
# -------------------------
def ffmpeg_extract_audio(input_video_path, output_audio_path, sample_rate=16000):
    """
    Extracts audio from input video to WAV PCM 16-bit mono.
    Requires ffmpeg binary installed and in PATH.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ac", "1",
        "-ar", str(sample_rate),
        output_audio_path
    ]
    subprocess.run(cmd, check=True)

def srt_timestamp(ms):
    # ms: milliseconds
    td = timedelta(milliseconds=ms)
    hours = td.seconds // 3600 + td.days * 24
    minutes = (td.seconds % 3600) // 60
    seconds = td.seconds % 60
    millis = td.microseconds // 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"

def write_srt(segments, srt_path):
    """
    segments: list of dicts: [{'start_ms': int, 'end_ms': int, 'text': str}, ...]
    """
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            f.write(f"{i}\n")
            f.write(f"{srt_timestamp(seg['start_ms'])} --> {srt_timestamp(seg['end_ms'])}\n")
            f.write(seg['text'].strip() + "\n\n")

# -------------------------
# ASR: modular wrapper
# -------------------------
def transcribe_with_whisper_local(audio_path, model_name="small"):
    """
    Attempt to transcribe with faster-whisper or openai/whisper if available.
    Return list of segments [{'start_ms', 'end_ms', 'text'}].
    This function tries to import faster_whisper first for performance; if unavailable,
    it attempts the openai whisper package.
    """
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
        segments = []
        result = model.transcribe(audio_path, beam_size=5, vad_filter=True)
        for segment in result:
            start_s = segment.start
            end_s = segment.end
            text = segment.text
            segments.append({'start_ms': int(start_s * 1000), 'end_ms': int(end_s * 1000), 'text': text})
        return segments
    except Exception as e:
        print("faster-whisper not available or failed:", e)
        try:
            import whisper
            wmodel = whisper.load_model(model_name)
            res = wmodel.transcribe(audio_path)
            # whisper returns 'segments'
            segments = []
            for s in res.get("segments", []):
                segments.append({'start_ms': int(s['start'] * 1000), 'end_ms': int(s['end'] * 1000), 'text': s['text']})
            return segments
        except Exception as e2:
            raise RuntimeError("No working Whisper implementation found; install faster-whisper or whisper.") from e2

def transcribe_with_vosk_streaming(audio_path, model_dir="model"):
    """
    Run Vosk on a full WAV file and create segments.
    Requires a Vosk model downloaded to model_dir (e.g., 'model' folder).
    """
    try:
        from vosk import Model, KaldiRecognizer
        import wave
        wf = wave.open(audio_path, "rb")
        model = Model(model_dir)
        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)
        segments = []
        import json
        # Vosk returns partial results and final results; we'll build naive segments using word timestamps
        words_acc = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                words = res.get("result", [])
                for w in words:
                    words_acc.append(w)
        # final chunk
        final = json.loads(rec.FinalResult())
        for w in final.get("result", []):
            words_acc.append(w)
        # build segments by grouping words into ~3-6 second buckets
        if not words_acc:
            return []
        curr_segment = {'start_ms': int(words_acc[0]['start'] * 1000), 'end_ms': int(words_acc[0]['end'] * 1000), 'text': words_acc[0]['word']}
        for w in words_acc[1:]:
            # if gap > 1.0s or segment > 6s, flush
            if (w['start'] - curr_segment['start_ms']/1000.0) > 6.0 or (w['start'] - curr_segment['end_ms']/1000.0) > 1.0:
                segments.append(curr_segment)
                curr_segment = {'start_ms': int(w['start']*1000), 'end_ms': int(w['end']*1000), 'text': w['word']}
            else:
                curr_segment['end_ms'] = int(w['end']*1000)
                curr_segment['text'] += ' ' + w['word']
        segments.append(curr_segment)
        return segments
    except Exception as e:
        raise RuntimeError("Vosk transcription failed or Vosk not installed/configured: " + str(e))

# -------------------------
# Gemini-based post-processing
# -------------------------
def clean_with_gemini(segment_text):
    """
    Uses Gemini to add punctuation, fix casing, and optionally translate.
    Keep prompt small to reduce token cost; send chunk and ask for punctuation only.
    """
    prompt = f"Add punctuation and proper capitalization to the following transcript. Keep it faithful to the original words:\n\n---\n{segment_text}\n---\nReturn only the corrected text."
    response_text = ""
    # Using generate_content_stream pattern like the feed module
    response = client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=prompt
    )
    for chunk in response:
        if chunk.text:
            response_text += chunk.text
    return response_text.strip()

def postprocess_segments_with_gemini(segments, max_chars_per_call=8000):
    """
    For each segment, call Gemini to clean text. If segments are long, split.
    Returns new segments with cleaned 'text' fields.
    """
    from math import ceil
    cleaned = []
    for seg in segments:
        text = seg['text'].strip()
        if not text:
            cleaned.append({**seg, 'text': ''})
            continue
        # If very long, break into smaller chunks by chars
        if len(text) <= max_chars_per_call:
            cleaned_text = clean_with_gemini(text)
            cleaned.append({**seg, 'text': cleaned_text})
        else:
            # naive split: by words into multiple cleaned subsegments, then rejoin
            words = text.split()
            chunk_words = []
            curr_len = 0
            combined_texts = []
            for w in words:
                if curr_len + len(w) + 1 > max_chars_per_call:
                    combined_texts.append(' '.join(chunk_words))
                    chunk_words = [w]
                    curr_len = len(w)
                else:
                    chunk_words.append(w)
                    curr_len += len(w) + 1
            if chunk_words:
                combined_texts.append(' '.join(chunk_words))
            # clean each and rejoin with spaces
            cleaned_chunks = [clean_with_gemini(ct) for ct in combined_texts]
            cleaned_text = " ".join(cleaned_chunks)
            cleaned.append({**seg, 'text': cleaned_text})
    return cleaned

# -------------------------
# Public batch function
# -------------------------
def generate_srt_from_video(video_path, srt_output_path, use_asr="whisper", whisper_model="small", vosk_model_dir="model", burn_into_video=False, out_video_path=None):
    """
    High-level function: video -> audio -> asr -> gemini cleanup -> srt
    use_asr: "whisper" or "vosk"
    """
    with tempfile.TemporaryDirectory() as td:
        audio_path = os.path.join(td, "extracted.wav")
        ffmpeg_extract_audio(video_path, audio_path, sample_rate=16000)

        if use_asr == "whisper":
            segments = transcribe_with_whisper_local(audio_path, model_name=whisper_model)
        elif use_asr == "vosk":
            segments = transcribe_with_vosk_streaming(audio_path, model_dir=vosk_model_dir)
        else:
            raise ValueError("Unsupported ASR backend")

        # If no timestamps provided (some ASR might not), build naive segmentation
        if not segments:
            raise RuntimeError("No segments produced by ASR")

        # Post-process segments with Gemini for punctuation & casing
        cleaned = postprocess_segments_with_gemini(segments)

        # Optionally merge very short adjacent segments for better reading
        merged = []
        for seg in cleaned:
            if not merged:
                merged.append(seg)
            else:
                last = merged[-1]
                # merge if last text length short and gap small
                if len(last['text']) < 40 and (seg['start_ms'] - last['end_ms']) < 500:
                    # extend last
                    last['end_ms'] = seg['end_ms']
                    last['text'] = (last['text'] + " " + seg['text']).strip()
                else:
                    merged.append(seg)

        write_srt(merged, srt_output_path)

        if burn_into_video:
            if out_video_path is None:
                raise ValueError("out_video_path required when burn_into_video=True")
            # overlay srt using ffmpeg (libass)
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-vf", f"subtitles={srt_output_path}:force_style='FontSize=24,PrimaryColour=&H00FFFFFF'",
                "-c:a", "copy",
                out_video_path
            ]
            subprocess.run(cmd, check=True)

        return srt_output_path

# -------------------------
# CLI entrypoint for convenience
# -------------------------
'''
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Generate SRT captions from a video file")
    p.add_argument("--input", "-i", required=True, help="input video file")
    p.add_argument("--out", "-o", required=True, help="output srt file path")
    p.add_argument("--asr", default="whisper", choices=["whisper","vosk"], help="ASR backend")
    p.add_argument("--whisper-model", default="small", help="whisper model size (if using whisper)")
    p.add_argument("--vosk-model-dir", default="model", help="path to vosk model dir (if using vosk)")
    p.add_argument("--burn", action="store_true", help="burn captions into a new video (requires --burn-out)")
    p.add_argument("--burn-out", help="output video path when burning captions")
    args = p.parse_args()

    srt_path = generate_srt_from_video(args.input, args.out, use_asr=args.asr, whisper_model=args.whisper_model, vosk_model_dir=args.vosk_model_dir, burn_into_video=args.burn, out_video_path=args.burn_out)
    print("SRT generated at:", srt_path)
'''