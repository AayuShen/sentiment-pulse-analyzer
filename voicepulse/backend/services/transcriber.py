import os, sys, time, gc
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.add_dll_directory(r"E:\Programming\ffmpeg-8.1.1-full_build-shared\bin")

import torch
import pandas as pd
import whisperx
from pyannote.audio import Pipeline as PyannotePipeline
from config import cfg
from pathlib import Path

_debug_file = Path(__file__).resolve().parent.parent.parent / "logs" / "transcriber_debug.log"
_debug_file.parent.mkdir(parents=True, exist_ok=True)

def _dbg(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(_debug_file, "a") as f:
        f.write(line + "\n")

_model = None
_align_model = None
_align_meta = None
_diarize = None
_device = None
_cached_lang = None

def _init(lang_code=None):
    global _model, _align_model, _align_meta, _diarize, _device, _cached_lang
    if _model is None:
        _device = "cuda" if torch.cuda.is_available() else "cpu"
        ct = "float16" if _device == "cuda" else "int8"
        _dbg(f"Loading WhisperX large-v2 on {_device} ({ct})")
        t0 = time.time()
        _model = whisperx.load_model("large-v2", _device, compute_type=ct)
        _dbg(f"WhisperX large-v2 loaded in {time.time()-t0:.1f}s")

        _dbg("Loading pyannote on CPU (defer GPU move)")
        t0 = time.time()
        _diarize = PyannotePipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=cfg.HF_TOKEN
        )
        _dbg(f"pyannote loaded in {time.time()-t0:.1f}s (on CPU)")

    if _align_model is None or _cached_lang != lang_code:
        effective_lang = lang_code or "en"
        _dbg(f"Loading align model for: {effective_lang}")
        t0 = time.time()
        _align_model, _align_meta = whisperx.load_align_model(
            language_code=effective_lang, device=_device
        )
        _dbg(f"Align model loaded in {time.time()-t0:.1f}s")
        _cached_lang = lang_code

def _offload_whisperx():
    """Move WhisperX to CPU to free VRAM for diarization."""
    global _model, _align_model, _align_meta
    if _model is not None and _device == "cuda":
        _dbg("Offloading WhisperX to CPU to free VRAM")
        _model = None
        _align_model = None
        _align_meta = None
        gc.collect()
        torch.cuda.empty_cache()
        _dbg(f"VRAM after offload: {torch.cuda.memory_allocated()/1024**2:.0f} MB")

def _reload_whisperx(lang_code=None):
    """Reload WhisperX on GPU after diarization."""
    global _model, _align_model, _align_meta, _cached_lang
    if _model is None:
        ct = "float16" if _device == "cuda" else "int8"
        _model = whisperx.load_model("large-v2", _device, compute_type=ct)
        effective_lang = lang_code or "en"
        _align_model, _align_meta = whisperx.load_align_model(
            language_code=effective_lang, device=_device
        )
        _cached_lang = lang_code

def run(rec: str, lang: str = None) -> list[dict]:
    _init(lang)

    _dbg("Step 1/4: Loading audio")
    t0 = time.time()
    audio = whisperx.load_audio(rec)
    _dbg(f"Audio loaded in {time.time()-t0:.1f}s, duration={len(audio)/16000:.1f}s")

    _dbg("Step 2/4: Transcribing")
    t0 = time.time()
    result = _model.transcribe(audio, batch_size=4, language=lang)
    segs = result.get("segments", [])
    word_conf = [w.get("score", 0) for s in segs for w in s.get("words", []) if "score" in w]
    avg_conf = round(sum(word_conf) / len(word_conf), 3) if word_conf else 0.0
    _dbg(f"Transcription done in {time.time()-t0:.1f}s, segments={len(segs)}, avg confidence={avg_conf}")

    _dbg("Step 2b: Aligning")
    t0 = time.time()
    result = whisperx.align(
        result["segments"], _align_model, _align_meta, audio, _device,
        return_char_alignments=False
    )
    _dbg(f"Alignment done in {time.time()-t0:.1f}s")

    _dbg("Step 3/4: Offloading WhisperX, running diarization")
    _offload_whisperx()

    _dbg(f"Moving pyannote to {_device}")
    _diarize.to(torch.device(_device))

    t0 = time.time()
    diar = _diarize(rec)
    annotation = diar.speaker_diarization if hasattr(diar, 'speaker_diarization') else diar
    _dbg(f"Diarization done in {time.time()-t0:.1f}s")

    _dbg("Moving pyannote back to CPU")
    _diarize.to(torch.device("cpu"))
    torch.cuda.empty_cache()
    _dbg(f"VRAM after pyannote offload: {torch.cuda.memory_allocated()/1024**2:.0f} MB")

    diar_rows = []
    for segment, track, speaker in annotation.itertracks(yield_label=True):
        diar_rows.append({"start": segment.start, "end": segment.end, "speaker": speaker})
    diar_df = pd.DataFrame(diar_rows)
    _dbg(f"Speakers found: {diar_df['speaker'].nunique() if len(diar_df) > 0 else 0}")

    _dbg("Step 3b: Assigning speakers to words")
    t0 = time.time()
    whisperx.assign_word_speakers(diar_df, result)
    _dbg(f"Speaker assignment done in {time.time()-t0:.1f}s")

    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "speaker": seg.get("speaker", "SPEAKER_00"),
            "start": round(seg["start"], 2),
            "end": round(seg["end"], 2),
            "text": seg["text"].strip()
        })
    _dbg(f"Pipeline complete. {len(segments)} segments returned. WhisperX offloaded.")
    return segments
