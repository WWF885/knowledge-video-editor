#!/usr/bin/env python3
"""transcribe.py · 语音转写 + 句级切分 + 双语字幕输出

优先 faster-whisper，其次 openai-whisper，再次 whisper.cpp 命令行。
产出 transcript.json（词级时间戳 + 句级段落）、subtitle.json、subtitle.srt。

英文翻译：
  --translate-mode offline  只做占位（保留中文，en 留空），由宿主大模型补译
  --translate-mode glossary 用术语表做机械替换（质量有限，仅供占位）

用法：
    python3 scripts/transcribe.py --video work/edited.mp4 --bilingual --out work/
    python3 scripts/transcribe.py --video input.mp4 --lang zh --model small
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kve_common as k


# 语义断句：中文按标点与连接词切，单句不超过 18 字。
BREAK_CHARS = "，。？！；：、…"
SOFT_JOINERS = ("但是", "所以", "因为", "而且", "不过", "如果", "就是", "然后", "其实")


def split_sentence(text: str, max_chars=18) -> list:
    text = text.strip()
    if not text:
        return []
    parts, buf = [], ""
    for ch in text:
        buf += ch
        if ch in BREAK_CHARS and len(buf) >= 6:
            parts.append(buf)
            buf = ""
        elif len(buf) >= max_chars:
            # 尝试在连接词处切
            for j in SOFT_JOINERS:
                idx = buf.find(j, 4)
                if idx > 0:
                    parts.append(buf[:idx])
                    buf = buf[idx:]
                    break
            else:
                parts.append(buf)
                buf = ""
    if buf.strip():
        parts.append(buf)
    return [p.strip().strip(BREAK_CHARS) for p in parts if p.strip().strip(BREAK_CHARS)]


def run_faster_whisper(path, model, lang):
    from faster_whisper import WhisperModel  # 延迟导入
    m = WhisperModel(model, device="auto", compute_type="int8")
    segments, info = m.transcribe(str(path), language=lang or None,
                                  vad_filter=True, word_timestamps=True,
                                  beam_size=5)
    words_all, segs = [], []
    for s in segments:
        words = []
        for w in (s.words or []):
            words.append({"w": w.word, "start": round(w.start, 3), "end": round(w.end, 3),
                          "prob": round(getattr(w, "probability", 0.0), 3)})
            words_all.append(words[-1])
        segs.append({"start": round(s.start, 3), "end": round(s.end, 3),
                     "text": (s.text or "").strip(), "words": words})
    return {"engine": f"faster-whisper:{model}", "language": info.language,
            "duration": round(info.duration, 3), "segments": segs, "words": words_all}


def run_openai_whisper(path, model, lang):
    import whisper  # 延迟导入
    m = whisper.load_model(model)
    res = m.transcribe(str(path), language=lang or None, word_timestamps=True, verbose=False)
    segs, words_all = [], []
    for s in res.get("segments", []):
        words = []
        for w in (s.get("words") or []):
            words.append({"w": w.get("word", ""), "start": round(w["start"], 3),
                          "end": round(w["end"], 3), "prob": round(w.get("probability", 0.0), 3)})
            words_all.append(words[-1])
        segs.append({"start": round(s["start"], 3), "end": round(s["end"], 3),
                     "text": (s.get("text") or "").strip(), "words": words})
    return {"engine": f"openai-whisper:{model}", "language": res.get("language"),
            "duration": None, "segments": segs, "words": words_all}


def run_cli(path, lang):
    import shutil, subprocess, tempfile, json as _json
    exe = shutil.which("whisper-cli") or shutil.which("whisper")
    if not exe:
        return None
    with tempfile.TemporaryDirectory() as td:
        base = Path(td) / "out"
        r = subprocess.run([exe, "-f", str(path), "-oj", "-of", str(base),
                            "-l", lang or "auto"], capture_output=True, text=True)
        jf = Path(str(base) + ".json")
        if r.returncode != 0 or not jf.exists():
            return None
        data = _json.loads(jf.read_text(encoding="utf-8"))
        segs = []
        for s in data.get("transcription", []):
            segs.append({"start": round(s.get("offsets", {}).get("from", 0) / 1000, 3),
                         "end": round(s.get("offsets", {}).get("to", 0) / 1000, 3),
                         "text": (s.get("text") or "").strip(), "words": []})
        return {"engine": "whisper-cli", "language": lang, "duration": None,
                "segments": segs, "words": []}


def to_sentences(raw: dict, max_chars=18) -> list:
    """把段级结果重切成句级，并按字数比例估算句内时间。"""
    out = []
    for seg in raw["segments"]:
        pieces = split_sentence(seg["text"], max_chars)
        if len(pieces) <= 1:
            out.append({"start": seg["start"], "end": seg["end"], "zh": seg["text"]})
            continue
        total = sum(len(p) for p in pieces) or 1
        cursor = seg["start"]
        span = seg["end"] - seg["start"]
        for p in pieces:
            share = span * len(p) / total
            out.append({"start": round(cursor, 3), "end": round(cursor + share, 3), "zh": p})
            cursor += share
    # 保证不重叠、不越界
    for i in range(1, len(out)):
        if out[i]["start"] < out[i - 1]["end"] - 0.01:
            out[i]["start"] = out[i - 1]["end"]
    return out


def apply_glossary(sentences: list, glossary: dict) -> list:
    """机械占位翻译：术语替换 + 原文保留，提示"需模型润色"。"""
    zh_en = glossary.get("zh_en", {})
    for s in sentences:
        en = s["zh"]
        for zh, e in sorted(zh_en.items(), key=lambda x: -len(x[0])):
            en = en.replace(zh, f" {e} ")
        if not re.search(r"[A-Za-z]{3,}", en):
            en = ""
        s["en"] = re.sub(r"\s+", " ", en).strip()
    return sentences


def write_srt(sentences, path):
    lines = []
    for i, s in enumerate(sentences, 1):
        lines.append(str(i))
        lines.append(f"{k.fmt_srt_time(s['start'])} --> {k.fmt_srt_time(s['end'])}")
        lines.append(s["zh"])
        if s.get("en"):
            lines.append(s["en"])
        lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="语音转写与双语字幕")
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", default="work")
    ap.add_argument("--lang", default="zh")
    ap.add_argument("--model", default="small")
    ap.add_argument("--bilingual", action="store_true")
    ap.add_argument("--max-chars", type=int, default=18)
    ap.add_argument("--engine", choices=["auto", "faster", "openai", "cli"], default="auto")
    args = ap.parse_args()

    log = k.Log()
    raw = None
    if args.engine in ("auto", "faster"):
        try:
            raw = run_faster_whisper(args.video, args.model, args.lang)
            log("使用 faster-whisper", "ok")
        except Exception as e:
            log(f"faster-whisper 不可用：{e}", "warn")
    if raw is None and args.engine in ("auto", "openai"):
        try:
            raw = run_openai_whisper(args.video, args.model, args.lang)
            log("使用 openai-whisper", "ok")
        except Exception as e:
            log(f"openai-whisper 不可用：{e}", "warn")
    if raw is None and args.engine in ("auto", "cli"):
        raw = run_cli(args.video, args.lang)
        if raw:
            log("使用 whisper-cli", "ok")
    if raw is None:
        log("没有可用的转写引擎。请安装 faster-whisper，或由宿主模型完成转写。", "err")
        sys.exit(2)

    sentences = to_sentences(raw, args.max_chars)
    if args.bilingual:
        sentences = apply_glossary(sentences, k.load_config("glossary"))

    out_dir = k.ensure_dir(args.out)
    k.write_json(out_dir / "transcript.json",
                 {"engine": raw["engine"], "language": raw["language"],
                  "segments": raw["segments"], "words": raw["words"],
                  "sentences": sentences})
    k.write_json(out_dir / "subtitle.json",
                 {"layout": "chinese_above_english", "items": [
                     {"id": f"sub_{i:04d}", "start": s["start"], "end": s["end"],
                      "zh": s["zh"], "en": s.get("en", "")}
                     for i, s in enumerate(sentences, 1)]})
    write_srt(sentences, out_dir / "subtitle.srt")

    print(f"引擎 {raw['engine']} · 语言 {raw['language']}")
    print(f"句数 {len(sentences)} · 输出 {out_dir}/transcript.json, subtitle.json, subtitle.srt")
    if args.bilingual and not any(s.get("en") for s in sentences):
        print("! 英文为空。glossary 模式只做术语占位，正式译文需宿主大模型补全后覆盖 subtitle.json。")


if __name__ == "__main__":
    main()
