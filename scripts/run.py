#!/usr/bin/env python3
"""run.py · 全流程编排

按 13 步流水线串起所有脚本，产出标准交付清单。

用法：
    python3 scripts/run.py --video input.mp4 --out ./我的项目 --ratio 16:9 --theme auto
    python3 scripts/run.py --video input.mp4 --out ./项目 --storyboard work/storyboard.json
    python3 scripts/run.py --video input.mp4 --out ./项目 --dry-run

注意：没有 --storyboard 时，run.py 只生成"骨架分镜"（structural scaffold），
      它保证能通过校验与渲染，但视觉表达是通用形态。正式出片应由大模型
      按 references/06、07 重写 storyboard 后再跑。
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kve_common as k

SCRIPT = k.ROOT / "scripts"
TOTAL_STEPS = 9


def step(log, idx, msg):
    log.step(idx, TOTAL_STEPS, msg)


def call(script, args, log, fatal=True, quiet=True) -> int:
    cmd = [sys.executable, str(SCRIPT / script)] + args
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        tail = (r.stdout or "")[-600:] + (r.stderr or "")[-600:]
        log(f"{script} 失败（码 {r.returncode}）：\n{tail}", "err")
        if fatal:
            sys.exit(r.returncode)
    elif not quiet and r.stdout:
        print(r.stdout)
    return r.returncode


def split_cover(title: str):
    """把标题压成 ≤2 行、每行 ≤4 字。"""
    clean = "".join(ch for ch in title if ch.strip())
    if len(clean) <= 4:
        return [clean]
    return [clean[:4], clean[4:8]]


DEFAULT_CHAPTERS = {
    "knowledge": ["是什么", "为什么", "怎么用", "总结"],
    "practice": ["准备", "操作", "验证", "复盘"],
    "analysis": ["现状", "原因", "预测", "结论"],
    "opinion": ["误区", "真相", "做法", "总结"],
    "story": ["起因", "转折", "结果", "启发"],
    "industry": ["格局", "变量", "机会", "判断"],
}


def scaffold(transcript: dict, title: str, ratio: str, theme: str, video_type: str, cover_dur=2.0) -> dict:
    """生成结构性骨架分镜：可校验、可渲染，但需模型再优化视觉表达。"""
    sentences = transcript.get("sentences") or [
        {"start": s["start"], "end": s["end"], "zh": s.get("text", "")}
        for s in transcript.get("segments", [])
    ]
    if not sentences:
        raise RuntimeError("文稿为空，无法生成骨架分镜")
    total = sentences[-1]["end"]
    chapters = DEFAULT_CHAPTERS.get(video_type, DEFAULT_CHAPTERS["knowledge"])
    n_chap = len(chapters)

    body = [s for s in sentences if s["end"] > cover_dur + 0.1]
    if not body:
        body = sentences[-2:] if len(sentences) > 1 else sentences
    per = max(1, len(body) // n_chap)
    scenes = [{
        "scene_id": "S001", "start": 0.0, "end": cover_dur, "chapter": chapters[0],
        "visual_type": "cover",
        "content": {"title_lines": split_cover(title)},
        "cover_visible": True,
        "animation_plan": [
            {"time": 0.0, "action": "cover_static", "ease": "linear", "dur": 0.0},
            {"time": 0.6, "action": "keyword_glow", "ease": "easeOutCubic", "dur": 0.6},
            {"time": 1.4, "action": "subtle_push", "ease": "easeOutCubic", "dur": 0.6},
        ],
    }]

    visual_pool = ["presenter", "keyword", "cards", "flow_steps", "compare", "chart",
                   "timeline", "summary"]
    sid = 2
    for ci, chap in enumerate(chapters):
        chunk = body[ci * per:(ci + 1) * per] if ci < n_chap - 1 else body[ci * per:]
        if not chunk:
            continue
        # 每章 1–2 个镜头
        groups = [chunk] if len(chunk) <= 2 else [chunk[:len(chunk) // 2], chunk[len(chunk) // 2:]]
        for gi, g in enumerate(groups):
            st = max(cover_dur, g[0]["start"]) if (ci == 0 and gi == 0) else g[0]["start"]
            en = g[-1]["end"]
            if en - st < 0.8:
                en = st + 0.8
            vt = "presenter" if gi == 0 else visual_pool[(ci + gi) % len(visual_pool)]
            if ci == n_chap - 1 and gi == len(groups) - 1:
                vt = "summary"
            plan = []
            t = st
            actions = ["fade_in", "highlight_keyword", "read_hold", "subtle_zoom"]
            ai = 0
            while t < en - 0.1:
                plan.append({"time": round(t, 2), "action": actions[ai % len(actions)],
                             "ease": "easeOutCubic" if ai % 2 == 0 else "linear",
                             "dur": 0.3 if ai % 2 == 0 else 0.0})
                t += 1.2
                ai += 1
            scenes.append({
                "scene_id": f"S{sid:03d}", "start": round(st, 2), "end": round(en, 2),
                "chapter": chap, "visual_type": vt,
                "content": {"title": chap, "text": g[0]["zh"][:24]},
                "cover_visible": False,
                "animation_plan": plan,
                "sfx": [{"at": round(st + 0.5, 2), "name": "whoosh", "gain": -18}] if gi == 0 else [],
            })
            sid += 1

    # 修连续性与尾部
    for i in range(1, len(scenes)):
        if scenes[i]["start"] < scenes[i - 1]["end"] - 0.01:
            scenes[i]["start"] = scenes[i - 1]["end"]
    scenes[-1]["end"] = round(max(scenes[-1]["end"], total), 2)

    resolution = [1920, 1080] if ratio == "16:9" else [1080, 1920]
    return {
        "video_type": video_type,
        "aspect_ratio": ratio,
        "resolution": resolution,
        "theme": theme,
        "fps": 30,
        "duration": round(total, 2),
        "cover": {"lines": split_cover(title), "position": "center",
                  "visible_from_first_frame": True, "duration": cover_dur, "export_png": True},
        "navigation": {"enabled": True, "chapters": chapters, "height_ratio": 0.07,
                       "hide_during_cover": True, "style": "progress"},
        "subtitles": {"languages": ["zh", "en"], "layout": "chinese_above_english",
                      "safe_area_check": True},
        "storyboard": scenes,
    }


def write_transcript_md(transcript: dict, path: Path):
    lines = ["# 完整口播文稿", ""]
    for s in transcript.get("sentences", []):
        lines.append(f"**[{k.fmt_time(s['start'])}]** {s['zh']}  ")
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="知识型口播剪辑全流程")
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ratio", default="auto", help="16:9 / 9:16 / auto")
    ap.add_argument("--theme", default="auto", help="dark_gold / pearl_green / auto")
    ap.add_argument("--title", default=None, help="封面标题，用于骨架分镜")
    ap.add_argument("--storyboard", default=None, help="使用已有分镜（推荐）")
    ap.add_argument("--transcript", default=None)
    ap.add_argument("--bgm", default=None)
    ap.add_argument("--skip-edit", action="store_true", help="不精剪，直接包装原片")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    log = k.Log()
    out = k.ensure_dir(args.out)
    work = k.ensure_dir(out / "work")
    output = k.ensure_dir(out / "output")

    # 1 环境
    step(log, 1, "环境自检")
    env_code = call("check_environment.py", ["--json", "--out", str(work / "env_report.json")], log, fatal=False)
    env = k.read_json(work / "env_report.json") if (work / "env_report.json").exists() else {}
    if env.get("blockers"):
        log(f"阻塞项：{env['blockers']}", "err")
        if any("ffmpeg" in b or "ffprobe" in b for b in env["blockers"]):
            sys.exit(2)
    log(f"环境 {'就绪' if env_code == 0 else '有缺口，继续尝试'}", "ok")

    # 2 属性
    step(log, 2, "视频属性识别")
    call("analyze_video.py", ["--video", args.video, "--out", str(work / "video_meta.json")], log)
    meta = k.read_json(work / "video_meta.json")
    ratio = args.ratio if args.ratio != "auto" else meta["aspect_ratio"]
    if ratio not in ("16:9", "9:16"):
        ratio = "16:9" if meta["orientation"] == "horizontal" else "9:16"
    log(f"{meta['orientation']} {meta['aspect_ratio']} → 出片比例 {ratio}", "ok")

    # 3 转写
    step(log, 3, "语音转写")
    tr_path = Path(args.transcript) if args.transcript else work / "transcript.json"
    if not Path(tr_path).exists():
        call("transcribe.py", ["--video", args.video, "--out", str(work), "--bilingual"], log, fatal=False)
    transcript = k.read_json(tr_path) if Path(tr_path).exists() else {"sentences": [], "segments": []}
    log(f"句数 {len(transcript.get('sentences', []))}", "ok")

    # 4 精剪
    step(log, 4, "自动精剪")
    edited = work / "edited.mp4"
    if args.skip_edit:
        edited = Path(args.video)
        log("跳过精剪，直接使用原片", "warn")
    else:
        call("edit_video.py", ["--video", args.video, "--auto", "--transcript", str(tr_path),
                               "--out", str(edited)], log)

    # 5 导演计划 / 分镜
    step(log, 5, "导演计划与分镜")
    if args.storyboard:
        sb = k.read_json(args.storyboard)
        log("使用外部 storyboard", "ok")
    else:
        title = args.title or "内容重塑"
        vtype = (meta.get("analysis") or {}).get("video_type") or "knowledge"
        theme = args.theme if args.theme != "auto" else (
            "dark_gold" if vtype in ("knowledge", "practice", "analysis", "industry") else "pearl_green")
        sb = scaffold(transcript, title, ratio, theme, vtype)
        log("已生成骨架分镜（需模型优化视觉表达）", "warn")
    sb.setdefault("subtitles", {})["source"] = str(work / "subtitle.json")
    k.write_json(work / "storyboard.json", sb)
    k.write_json(work / "director_plan.json", {x: sb[x] for x in
                 ("video_type", "aspect_ratio", "resolution", "theme", "cover", "navigation")})

    # 6 校验
    step(log, 6, "分镜校验")
    if call("validate_storyboard.py", ["--storyboard", str(work / "storyboard.json")], log, fatal=False) != 0:
        log("分镜不合格，停止（需修 storyboard 后重跑）", "err")
        sys.exit(3)

    # 7 渲染
    step(log, 7, "渲染与混音")
    final = output / "01_最终成片.mp4"
    cover = output / "02_首帧封面.png"
    call("render_video.py", ["--storyboard", str(work / "storyboard.json"), "--ratio", ratio,
                             "--audio", str(edited), "--out", str(final), "--cover", str(cover)]
         + (["--bgm", args.bgm] if args.bgm else []), log)

    # 8 质检
    step(log, 8, "自动质检")
    qc = output / "08_自动质检报告.md"
    call("quality_check.py", ["--video", str(final), "--storyboard", str(work / "storyboard.json"),
                              "--report", str(qc)], log, fatal=False)

    # 9 交付整理
    step(log, 9, "整理交付清单")
    if edited != Path(args.video) and Path(edited).exists():
        shutil.copy2(edited, output / "03_精剪原声视频.mp4")
    if (work / "subtitle.srt").exists():
        shutil.copy2(work / "subtitle.srt", output / "04_中英双语字幕.srt")
    write_transcript_md(transcript, output / "05_完整口播文稿.md")
    shutil.copy2(work / "director_plan.json", output / "06_全片导演计划.json")
    shutil.copy2(work / "storyboard.json", output / "07_逐秒分镜计划.json")

    eng = output / "09_可编辑视频工程"
    k.ensure_dir(eng)
    for f in ("render_props.json", "timemap.json", "transcript.json", "subtitle.json", "edl.json"):
        if (work / f).exists():
            shutil.copy2(work / f, eng / f)

    print(f"\n=== 交付清单：{output} ===")
    for name in k.default_cfg()["paths"]["deliverables"]:
        p = output / name
        print(f"  {'✓' if p.exists() else '×'} {name}")

    qc_text = qc.read_text(encoding="utf-8") if qc.exists() else ""
    score = None
    for line in qc_text.splitlines():
        if line.startswith("## 总分："):
            score = line
            break
    print(f"\n{score or '质检报告缺失'}")
    print(f"工程目录：{out}")


if __name__ == "__main__":
    main()
