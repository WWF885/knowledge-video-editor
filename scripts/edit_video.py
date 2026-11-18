#!/usr/bin/env python3
"""edit_video.py · 按 EDL 精剪 + 音频处理 + 时间轴重映射

EDL 格式（二选一）：
  {"cuts": [{"start": 0, "end": 2.4, "keep": false}, {"start": 2.4, "end": 18, "keep": true}]}
  {"keep": [[2.4, 18.0], [19.2, 45.0]]}

产出：
  edited.mp4        精剪后视频（已降噪、响度归一）
  timemap.json      原时间 → 新时间映射，字幕/分镜必须用它换算
  cut_preview.txt   每个片段的起止与时长，便于人工核对

用法：
  python3 scripts/edit_video.py --video in.mp4 --edl work/edl.json --out work/edited.mp4
  python3 scripts/edit_video.py --video in.mp4 --auto --transcript work/transcript.json --out work/edited.mp4
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kve_common as k

FILLERS = ("嗯", "啊", "呃", "额", "那个那个", "就是说", "然后呢")


def edl_from_transcript(tr: dict, max_gap=0.8, min_keep=0.4) -> dict:
    """从文稿自动生成 EDL：删语气词句、压长停顿。"""
    dur = 0.0
    sentences = tr.get("sentences") or []
    if not sentences:
        for s in tr.get("segments", []):
            sentences.append({"start": s["start"], "end": s["end"], "zh": s["text"]})
    dur = sentences[-1]["end"] if sentences else 0.0
    keep = []
    for s in sentences:
        text = (s.get("zh") or "").strip()
        if not text:
            continue
        core = text.strip("，。？！,.?! ")
        if core in FILLERS or (len(core) <= 2 and core in FILLERS):
            continue
        keep.append([round(s["start"], 3), round(s["end"], 3)])

    # 合并相邻，保留不超过 max_gap 的呼吸间隙
    merged = []
    for s, e in keep:
        if merged and s - merged[-1][1] <= max_gap:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    merged = [[s, e] for s, e in merged if e - s >= min_keep]
    return {"keep": merged, "source_duration": dur}


def load_segments(edl: dict, source_dur: float) -> list:
    if "keep" in edl:
        segs = [[float(a), float(b)] for a, b in edl["keep"]]
    else:
        segs = [[float(c["start"]), float(c["end"])]
                for c in edl.get("cuts", []) if c.get("keep", True)]
    segs = sorted(segs)
    for s in segs:
        if s[0] < 0 or s[1] > source_dur + 0.5:
            raise ValueError(f"片段越界：{s}，源时长 {source_dur}")
    # 去掉重叠
    clean = []
    for s, e in segs:
        if clean and s < clean[-1][1] - 0.001:
            s = clean[-1][1]
        if e - s > 0.05:
            clean.append([s, e])
    return clean


def build_filter(segs, audio_opts, process_audio=True) -> tuple:
    n = len(segs)
    vparts, aparts = [], []
    for i, (s, e) in enumerate(segs):
        vparts.append(f"[0:v]trim=start={s:.3f}:end={e:.3f},setpts=PTS-STARTPTS[v{i}]")
        aparts.append(f"[0:a]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS[a{i}]")
    vin = "".join(f"[v{i}]" for i in range(n))
    ain = "".join(f"[a{i}]" for i in range(n))
    parts = vparts + aparts
    parts.append(f"{vin}concat=n={n}:v=1:a=0[vcat]")
    parts.append(f"{ain}concat=n={n}:v=1:a=1[vout0][aout0]")
    if process_audio:
        chain = [f"highpass=f={audio_opts['highpass_hz']}"]
        if audio_opts["denoise"]["enabled"]:
            chain.append(f"afftdn=nf={audio_opts['denoise']['nf']}:nr={audio_opts['denoise']['nr']}")
        chain += ["equalizer=f=120:t=q:w=1:g=-2",
                  "equalizer=f=2500:t=q:w=1:g=1.5",
                  f"loudnorm=I={audio_opts['target_lufs']}:TP={audio_opts['true_peak']}:LRA={audio_opts['lra']}",
                  "alimiter=limit=-1dB"]
        parts.append("[aout0]" + ",".join(chain) + "[aout]")
    else:
        parts.append("[aout0]anull[aout]")
    parts.append("[vout0]null[vout]")
    return ";".join(parts), "[vout]", "[aout]"


def build_timemap(segs) -> tuple:
    mapping, cursor = [], 0.0
    for s, e in segs:
        mapping.append([round(s, 3), round(e, 3), round(cursor, 3)])
        cursor += e - s
    return mapping, round(cursor, 3)


def remap_time(t: float, mapping: list, mode="new") -> float:
    """mode=new：原时间→新时间；mode=old：新时间→原时间。"""
    if mode == "new":
        for os_, oe, ns in mapping:
            if os_ <= t <= oe:
                return round(ns + (t - os_), 3)
        return round(mapping[-1][2] + (mapping[-1][1] - mapping[-1][0]), 3) if t > mapping[-1][1] else round(mapping[0][2], 3)
    acc = 0.0
    for os_, oe, ns in mapping:
        dur = oe - os_
        if ns <= t <= ns + dur:
            return round(os_ + (t - ns), 3)
        acc += dur
    return round(mapping[-1][1], 3)


def main():
    ap = argparse.ArgumentParser(description="按 EDL 精剪")
    ap.add_argument("--video", required=True)
    ap.add_argument("--edl", help="EDL 文件")
    ap.add_argument("--auto", action="store_true", help="从 transcript.json 自动生成 EDL")
    ap.add_argument("--transcript", default="work/transcript.json")
    ap.add_argument("--out", default="work/edited.mp4")
    ap.add_argument("--max-gap", type=float, default=0.8, help="允许保留的呼吸间隙（秒）")
    ap.add_argument("--no-audio-process", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    log = k.Log()
    meta = k.probe(args.video)
    source_dur = meta["duration"]
    cfg = k.default_cfg()["audio"]

    if args.auto:
        edl = edl_from_transcript(k.read_json(args.transcript), max_gap=args.max_gap)
        log(f"自动 EDL：保留 {len(edl['keep'])} 段", "ok")
    elif args.edl:
        edl = k.read_json(args.edl)
    else:
        log("需要 --edl 或 --auto", "err")
        sys.exit(2)

    segs = load_segments(edl, source_dur)
    if not segs:
        log("EDL 没有可保留片段", "err")
        sys.exit(2)

    kept = sum(e - s for s, e in segs)
    removed = source_dur - kept
    log(f"源 {k.fmt_time(source_dur)} → 新 {k.fmt_time(kept)}（删掉 {k.fmt_time(removed)}，"
        f"{k.pct(removed / source_dur) if source_dur else 0}%）")

    mapping, new_dur = build_timemap(segs)
    out_dir = Path(args.out).parent
    k.ensure_dir(out_dir)
    k.write_json(out_dir / "timemap.json",
                 {"source": str(Path(args.video).resolve()), "source_duration": source_dur,
                  "output_duration": new_dur, "mapping": mapping, "segments": segs})

    preview = ["# 精剪片段", f"源时长 {k.fmt_time(source_dur)} → 输出 {k.fmt_time(new_dur)}", ""]
    for i, (s, e) in enumerate(segs, 1):
        preview.append(f"{i:02d}  {k.fmt_time(s)} → {k.fmt_time(e)}   dur {e - s:.2f}s")
    Path(out_dir / "cut_preview.txt").write_text("\n".join(preview), encoding="utf-8")

    ffilter, vmap, amap = build_filter(segs, cfg, not args.no_audio_process)
    cmd = ["ffmpeg", "-y", "-i", args.video, "-filter_complex", ffilter,
           "-map", vmap, "-map", amap,
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
           "-movflags", "+faststart", args.out]

    if args.dry_run:
        print("FILTER:\n", ffilter[:1200])
        print("\nCMD:\n", " ".join(cmd))
        return

    r = k.run(cmd, timeout=3600)
    if r.returncode != 0:
        log(f"ffmpeg 失败：{r.stderr.strip()[-800:]}", "err")
        sys.exit(1)

    out_meta = k.probe(args.out)
    k.write_json(out_dir / "edited_meta.json", out_meta)
    log(f"完成 → {args.out}（{out_meta['duration_hms']}）", "ok")
    print(f"\n时间映射：{out_dir}/timemap.json\n片段清单：{out_dir}/cut_preview.txt")


if __name__ == "__main__":
    main()
