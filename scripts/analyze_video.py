#!/usr/bin/env python3
"""analyze_video.py · 视频属性识别 + 内容初判

产出 video_meta.json：分辨率、比例、帧率、时长、编码、音频、静音段、
人像位置提示、推荐主题，以及（可选）基于文稿的类型初判。

用法：
    python3 scripts/analyze_video.py --video input.mp4 --out work/video_meta.json
    python3 scripts/analyze_video.py --video input.mp4 --transcript work/transcript.json --out work/analysis.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kve_common as k


# 六类内容的信号词。数量 > 语气，至少命中 2 个才敢定类型。
TYPE_SIGNALS = {
    "knowledge": ["什么是", "原理", "本质", "分为", "三个步骤", "方法", "为什么", "定义", "概念", "逻辑"],
    "practice": ["点击", "打开", "设置", "输入", "安装", "界面", "按钮", "工具栏", "导出", "快捷键"],
    "analysis": ["增长", "下降", "数据", "对比", "因为", "导致", "成本", "收入", "转化", "复购", "占比"],
    "opinion": ["我认为", "我觉得", "真正的", "别再", "关键是", "其实", "误区", "建议", "结论"],
    "story": ["那年", "后来", "结果", "当时", "第一次", "经历", "我记得", "第二天", "最终"],
    "industry": ["政策", "赛道", "上游", "下游", "行业", "市场", "格局", "监管", "供应链", "玩家"],
}

THEME_BY_TYPE = {
    "knowledge": "dark_gold", "practice": "dark_gold", "analysis": "dark_gold",
    "opinion": "pearl_green", "story": "pearl_green", "industry": "dark_gold",
}


def probe(path: str) -> dict:
    data = k.ffprobe_json(path)
    v = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    if v is None:
        raise RuntimeError("文件里没有视频流")

    w, h = int(v["width"]), int(v["height"])
    dar = v.get("display_aspect_ratio") or f"{w}:{h}"
    if ":" not in str(dar):
        dar = f"{w}:{h}"
    ratio = str(dar)
    if abs(w / h - 16 / 9) < 0.05:
        ratio = "16:9"
    elif abs(w / h - 9 / 16) < 0.05:
        ratio = "9:16"
    elif abs(w / h - 1) < 0.03:
        ratio = "1:1"

    num, _, den = str(v.get("avg_frame_rate", "0/1")).partition("/")
    fps = round(float(num) / float(den), 3) if den and float(den) else 0.0

    dur = float(data["format"].get("duration") or v.get("duration") or 0)
    return {
        "width": w, "height": h, "aspect_ratio": ratio,
        "orientation": "horizontal" if w > h else ("vertical" if h > w else "square"),
        "fps": fps, "duration": round(dur, 3), "duration_hms": k.fmt_time(dur),
        "video_codec": v.get("codec_name"), "pix_fmt": v.get("pix_fmt"),
        "bitrate_kbps": int(int(data["format"].get("bit_rate", 0)) / 1000) if data["format"].get("bit_rate") else None,
        "audio": None if not a else {
            "codec": a.get("codec_name"), "channels": a.get("channels"),
            "sample_rate": int(a.get("sample_rate", 0)),
        },
        "container": data["format"].get("format_name"),
        "size_mb": round(int(data["format"].get("size", 0)) / 1024 ** 2, 2),
    }


def silence_segments(path: str, threshold_db=-35, min_d=0.8) -> list:
    r = k.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af",
               f"silencedetect=noise={threshold_db}dB:d={min_d}", "-f", "null", "-"])
    out = r.stderr
    starts = [float(m) for m in re.findall(r"silence_start: ([0-9.]+)", out)]
    ends = [float(m) for m in re.findall(r"silence_end: ([0-9.]+)", out)]
    segs = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else None
        if e is not None:
            segs.append({"start": s, "end": e, "dur": round(e - s, 2)})
    total = sum(x["dur"] for x in segs)
    return {"segments": segs, "total_silence_s": round(total, 2),
            "ratio": round(total / 1.0, 2)}


def loudness(path: str) -> dict:
    r = k.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "ebur128", "-f", "null", "-"])
    m = re.findall(r"I: ([0-9.-]+) LUFS", r.stderr)
    tp = re.findall(r"Peak: ([0-9.-]+) dBFS", r.stderr)
    return {"integrated_lufs": float(m[-1]) if m else None,
            "true_peak_dbfs": float(tp[-1]) if tp else None}


def presenter_hint(path: str, t: float) -> dict:
    """抽样一帧，用左右半区肤色像素占比粗判人像位置。无 PIL 时跳过。"""
    try:
        from PIL import Image
    except Exception:
        return {"available": False, "reason": "缺少 pillow"}

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "f.png"
        r = k.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t}", "-i", str(path),
                   "-frames:v", "1", "-vf", "scale=320:-1", str(out)])
        if r.returncode != 0 or not out.exists():
            return {"available": False, "reason": "抽帧失败"}
        im = Image.open(out).convert("RGB")
        w, h = im.size
        px = im.load()

        def skin(p):
            r_, g_, b_ = p
            return (r_ > 95 and g_ > 40 and b_ > 20
                    and max(r_, g_, b_) - min(r_, g_, b_) > 15 and r_ > g and r_ > b)

        left = right = 0
        step = 4
        for y in range(0, h, step):
            for x in range(0, w, step):
                if skin(px[x, y]):
                    if x < w / 2:
                        left += 1
                    else:
                        right += 1
        total = max(1, left + right)
        if total < 30:
            return {"available": True, "position": "unknown", "skin_ratio": round(total / ((w//step)*(h//step)), 3)}
        return {
            "available": True,
            "position": "left" if left > right * 1.3 else ("right" if right > left * 1.3 else "center"),
            "left_ratio": round(left / total, 3), "right_ratio": round(right / total, 3),
        }


def classify(text: str) -> dict:
    """基于关键词的类型初判。只做初判，最终由大模型复核。"""
    scores = {}
    for t, words in TYPE_SIGNALS.items():
        hits = sum(text.count(x) for x in words)
        if hits:
            scores[t] = hits
    if not scores:
        return {"video_type": "opinion", "confidence": 0.4, "evidence": ["无显著信号，按最宽容类型兜底"]}
    total = sum(scores.values())
    top = max(scores, key=scores.get)
    conf = round(scores[top] / total, 2)
    evidence = [f"命中「{w}」{text.count(w)} 次" for w in TYPE_SIGNALS[top] if text.count(w)][:4]
    if len(evidence) < 2:
        conf = min(conf, 0.62)
    return {"video_type": top, "confidence": conf, "evidence": evidence or ["单一信号"]}


def segment_text(transcript: dict, win=25.0) -> list:
    segs = transcript.get("segments", [])
    out, cur = [], None
    for s in segs:
        if cur is None or s["start"] - cur["start"] > win:
            if cur:
                for t in TYPE_SIGNALS:
                    cur["scores"][t] = sum(cur["text"].count(w) for w in TYPE_SIGNALS[t])
                cur["type"] = max(cur["scores"], key=cur["scores"].get) if any(cur["scores"].values()) else "opinion"
                del cur["scores"]
                out.append(cur)
            cur = {"start": s["start"], "end": s["end"], "text": s["text"], "scores": {}}
        else:
            cur["end"] = s["end"]
            cur["text"] += s["text"]
    if cur:
        for t in TYPE_SIGNALS:
            cur["scores"][t] = sum(cur["text"].count(w) for w in TYPE_SIGNALS[t])
        cur["type"] = max(cur["scores"], key=cur["scores"].get) if any(cur["scores"].values()) else "opinion"
        del cur["scores"]
        out.append(cur)
    return [{"start": round(x["start"], 2), "end": round(x["end"], 2),
             "type": x["type"], "topic": x["text"][:24]} for x in out]


def main():
    ap = argparse.ArgumentParser(description="视频属性识别 + 内容初判")
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", default="work/video_meta.json")
    ap.add_argument("--transcript", help="提供文稿后额外做内容初判")
    ap.add_argument("--content", action="store_true", help="做内容类型判断（需 --transcript）")
    ap.add_argument("--skip-audio", action="store_true", help="跳过静音段与响度分析（更快）")
    ap.add_argument("--sample-t", type=float, default=2.0, help="人像抽样时间点")
    args = ap.parse_args()

    meta = probe(args.video)
    meta["source"] = str(Path(args.video).resolve())

    if not args.skip_audio:
        meta["silence"] = silence_segments(args.video)
        meta["loudness"] = loudness(args.video)
    meta["presenter_hint"] = presenter_hint(args.video, args.sample_t)

    if args.transcript and (args.content or True):
        tr = k.read_json(args.transcript)
        full = "".join(s["text"] for s in tr.get("segments", []))
        cls = classify(full)
        meta["analysis"] = {
            "video_type": cls["video_type"],
            "confidence": cls["confidence"],
            "evidence": cls["evidence"],
            "segments": segment_text(tr),
            "recommended_theme": THEME_BY_TYPE.get(cls["video_type"], "dark_gold"),
        }
    else:
        meta["analysis"] = {"video_type": None, "note": "未提供文稿，类型需由大模型判断"}

    k.write_json(args.out, meta)

    print(f"\n=== 视频属性 ===")
    print(f"  分辨率 {meta['width']}×{meta['height']}  ({meta['aspect_ratio']}, {meta['orientation']})")
    print(f"  时长   {meta['duration_hms']}   帧率 {meta['fps']}   编码 {meta['video_codec']}")
    print(f"  音频   {meta['audio']}")
    if "silence" in meta:
        print(f"  静音段 {len(meta['silence']['segments'])} 处，合计 {meta['silence']['total_silence_s']}s")
    if meta.get("presenter_hint", {}).get("available"):
        print(f"  人像位置 {meta['presenter_hint'].get('position')}")
    if meta["analysis"].get("video_type"):
        print(f"  类型初判 {meta['analysis']['video_type']}（置信度 {meta['analysis']['confidence']}）"
              f" → 推荐主题 {meta['analysis']['recommended_theme']}")
    print(f"\n已写入 {args.out}")


if __name__ == "__main__":
    main()
