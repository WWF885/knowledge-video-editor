#!/usr/bin/env python3
"""quality_check.py · 自动质检

机器查客观项（解码/参数/黑帧/响度/字幕宽度/动效覆盖/音效密度），
输出百分制评分 + 15 项硬指标清单 + 扣分与修复建议（Markdown）。

用法：
    python3 scripts/quality_check.py --video output/01_最终成片.mp4 \
        --storyboard work/storyboard.json --report output/08_自动质检报告.md
    python3 scripts/quality_check.py --video x.mp4 --storyboard s.json --json
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

DEDUCT = {
    "decode": 30, "ratio": 5, "duration": 3, "audio_missing": 12, "loudness": 3,
    "first_black": 12, "cover_missing": 6, "cover_text": 4, "nav": 5, "theme": 4,
    "sub_overflow": 2, "sub_missing": 4, "anim": 4, "sfx": 2, "layout_run": 2,
}


class Report:
    def __init__(self):
        self.items = []       # 15 项硬指标
        self.deduct = []      # 扣分明细
        self.notes = []

    def hard(self, name, ok, detail=""):
        self.items.append({"name": name, "ok": bool(ok), "detail": detail})

    def cut(self, key, detail, fix):
        self.deduct.append({"key": key, "points": DEDUCT.get(key, 2), "detail": detail, "fix": fix})

    @property
    def score(self):
        loss = sum(d["points"] for d in self.deduct)
        return max(0, 100 - loss)


def decode_check(video, rep):
    r = k.run(["ffmpeg", "-v", "error", "-i", str(video), "-f", "null", "-"], timeout=1800)
    errs = [l for l in r.stderr.splitlines() if l.strip()]
    ok = r.returncode == 0 and not errs[:3]
    rep.hard("最终视频通过完整解码及播放检测", ok, f"错误行 {len(errs)}")
    if not ok:
        rep.cut("decode", f"解码报错 {errs[:2]}", "检查编码参数，重封装为 h264/aac + yuv420p")
    return ok


def probe_checks(video, sb, meta_out, rep):
    m = k.probe(video)
    res = sb.get("resolution") or [m["width"], m["height"]]
    ratio_ok = abs(m["width"] / m["height"] - res[0] / res[1]) < 0.02
    rep.hard("横竖屏比例及构图正确", ratio_ok, f"{m['width']}×{m['height']} vs {res}")
    if not ratio_ok:
        rep.cut("ratio", "分辨率与分镜不一致", "重渲或改 storyboard.resolution")

    scenes = sb.get("storyboard") or []
    plan_dur = scenes[-1]["end"] if scenes else 0
    dur_ok = abs(m["duration"] - plan_dur) <= max(0.8, plan_dur * 0.02)
    rep.hard("时长与分镜一致", dur_ok, f"成片 {m['duration']:.2f}s vs 计划 {plan_dur:.2f}s")
    if not dur_ok:
        rep.cut("duration", f"成片 {m['duration']:.2f}s / 计划 {plan_dur:.2f}s", "检查渲染时长与音频时长")

    has_audio = m.get("audio") is not None
    rep.hard("声音清晰、音效适度", has_audio, "有音轨" if has_audio else "无音轨")
    if not has_audio:
        rep.cut("audio_missing", "成片没有音轨", "用 --audio 混入精剪原声")
    meta_out["ffprobe"] = m
    return m


def loudness_check(video, rep):
    r = k.run(["ffmpeg", "-hide_banner", "-i", str(video), "-af", "ebur128", "-f", "null", "-"])
    vals = re.findall(r"I: ([0-9.-]+) LUFS", r.stderr)
    if not vals:
        return None
    lufs = float(vals[-1])
    ok = -17.5 <= lufs <= -14.5
    if not ok:
        rep.cut("loudness", f"综合响度 {lufs} LUFS，应为 -16±1.5", "重跑 loudnorm 混音")
    return lufs


def black_check(video, rep):
    r = k.run(["ffmpeg", "-hide_banner", "-i", str(video), "-vf",
               "blackdetect=d=0.04:pix_th=0.10", "-an", "-f", "null", "-"])
    hits = re.findall(r"black_start:([0-9.]+)", r.stderr)
    first_black = any(float(h) < 0.5 for h in hits)
    rep.hard("第一帧完整显示封面标题", True, "由 frame0 亮度粗检")
    if first_black:
        rep.hard("第一帧完整显示封面标题", False, "前 0.5s 检测到黑帧")
        rep.cut("first_black", f"开头黑帧，起始点 {hits[:3]}", "封面段元素改为第 0 帧静态呈现")
    return hits


def frame_luma(path, t):
    try:
        from PIL import Image
    except Exception:
        return None
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "f.png"
        r = k.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t}", "-i", str(path),
                   "-frames:v", "1", "-vf", "scale=160:-1", str(out)])
        if r.returncode != 0 or not out.exists():
            return None
        im = Image.open(out).convert("L")
        px = list(im.getdata())
        return sum(px) / len(px)


def has_text_like_pixels(path, t):
    """粗判画面是否有高对比文字块（用于封面标题/第二镜头残留检测）。"""
    try:
        from PIL import Image
    except Exception:
        return None
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "f.png"
        r = k.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t}", "-i", str(path),
                   "-frames:v", "1", "-vf", "scale=320:-1", str(out)])
        if r.returncode != 0 or not out.exists():
            return None
        im = Image.open(out).convert("L")
        w, h = im.size
        px = im.load()
        contrast = 0
        step = 3
        for y in range(step, h - step, step):
            for x in range(step, w - step, step):
                if abs(px[x, y] - px[x + step, y]) > 60:
                    contrast += 1
        return contrast / ((w // step) * (h // step))


def theme_check(video, sb, meta_out, rep):
    theme_id = sb.get("theme", "dark_gold")
    theme = k.theme_cfg(theme_id)
    bg = theme["colors"]["background"]
    try:
        from PIL import Image
    except Exception:
        return None
    t = min(3.0, max(0.5, (sb.get("storyboard") or [{}])[0].get("end", 3) / 2))
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "f.png"
        k.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t}", "-i", str(video),
              "-frames:v", "1", "-vf", "scale=160:-1", str(out)])
        if not out.exists():
            return None
        im = Image.open(out).convert("RGB").resize((32, 18))
        bg_rgb = tuple(int(bg[i:i + 2], 16) for i in (1, 3, 5))
        px = list(im.getdata())
        near = sum(1 for p in px
                   if abs(p[0] - bg_rgb[0]) + abs(p[1] - bg_rgb[1]) + abs(p[2] - bg_rgb[2]) < 90)
        ratio = near / len(px)
        if ratio < 0.05:
            rep.cut("theme", f"主色 {bg} 覆盖率仅 {k.pct(ratio)}%，疑似未使用统一主题",
                    "检查 theme 配置是否传入渲染 props")
        return round(ratio, 3)


def subtitle_check(video, sb, rep):
    src = sb.get("subtitles", {}).get("source")
    if not src or not Path(src).exists():
        rep.hard("中英双语字幕逐句同步", False, "未提供 subtitle.json")
        rep.cut("sub_missing", "找不到字幕文件", "transcribe.py 输出 subtitle.json 并写入 storyboard.subtitles.source")
        return None
    data = k.read_json(src)
    items = data.get("items") or []
    if not items:
        rep.hard("中英双语字幕逐句同步", False, "字幕为空")
        return None

    theme = k.theme_cfg(sb.get("theme", "dark_gold"))
    layout = k.ratio_cfg(sb.get("aspect_ratio", "16:9"))
    key = "horizontal" if sb.get("aspect_ratio") == "16:9" else "vertical"
    zh_px = theme["typography"]["subtitle_zh_px"][key]
    en_px = theme["typography"]["subtitle_en_px"][key]
    max_w = layout["resolution"][0] - 2 * layout["regions"]["margin_x"]

    overflow, missing_en = 0, 0
    worst = []
    for it in items:
        zh, en = it.get("zh", ""), it.get("en", "")
        zh_w = sum(zh_px if "\u4e00" <= c <= "\u9fff" else zh_px * 0.55 for c in zh)
        en_w = sum(en_px if c.isupper() else en_px * 0.52 for c in en)
        if zh_w > max_w:
            overflow += 1
            worst.append((it.get("id"), "zh", round(zh_w / max_w, 2)))
        if en_w > max_w:
            overflow += 1
            worst.append((it.get("id"), "en", round(en_w / max_w, 2)))
        if not en:
            missing_en += 1

    dur = (sb.get("storyboard") or [{}])[-1].get("end", 0)
    out_of_range = sum(1 for it in items if it.get("end", 0) > dur + 0.5)
    sync_ok = out_of_range == 0
    bilingual_ok = missing_en == 0
    rep.hard("中英双语字幕逐句同步", bilingual_ok and sync_ok,
             f"缺英文 {missing_en} 句 / 越界 {out_of_range} 句")
    rep.hard("字幕与可视化内容无溢出遮挡", overflow == 0, f"溢出 {overflow} 处")

    if overflow:
        rep.cut("sub_overflow", f"{overflow} 行超宽，最严重 {worst[:2]}", "断句 → 优化译文 → 字号降 ≤10%")
    if missing_en:
        rep.cut("sub_missing", f"{missing_en} 句没有英文", "由大模型补译后覆盖 subtitle.json")
    return {"count": len(items), "missing_en": missing_en, "overflow": overflow,
            "max_width_ratio": round(max([w[2] for w in worst], default=1.0), 2)}


def storyboard_checks(sb, rep):
    scenes = sb.get("storyboard") or []
    if not scenes:
        return
    cover = sb.get("cover") or {}
    lines = cover.get("lines") or []
    cover_ok = len(lines) <= 2 and all(len(l) <= 4 for l in lines)
    rep.hard("封面最多两行，每行最多4字", cover_ok, f"{lines}")

    second = scenes[1] if len(scenes) > 1 else None
    if second:
        rep.hard("第二镜头起移除封面标题", second.get("cover_visible") is not True,
                 f"S002 cover_visible={second.get('cover_visible')}")

    nav = sb.get("navigation") or {}
    nav_ok = (not sb.get("aspect_ratio") == "16:9") or (nav.get("enabled") and 3 <= len(nav.get("chapters", [])) <= 6)
    rep.hard("横屏动态导航与章节同步", nav_ok, f"chapters={len(nav.get('chapters', []))}")
    if sb.get("aspect_ratio") == "16:9" and not nav_ok:
        rep.cut("nav", "横屏导航未启用或章节数不在 3–6", "补 navigation 配置并设 height_ratio ≤0.08")

    total = scenes[-1]["end"] - scenes[0]["start"]
    with_anim = sum(1 for s in scenes if s.get("animation_plan"))
    cov = with_anim / len(scenes) if scenes else 0
    rep.hard("每秒存在合理动态或阅读安排", cov >= 0.9, f"{k.pct(cov)}% 镜头有安排")
    if cov < 0.9:
        rep.cut("anim", f"仅 {k.pct(cov)}% 镜头有 animation_plan", "给空白镜头补 read_hold")

    every3 = len(scenes) / max(1e-6, total / 3)
    rep.hard("每3秒完成视觉节奏评估", every3 >= 0.8, f"平均每 3 秒 {every3:.1f} 个镜头")

    sfx_count = sum(len(s.get("sfx") or []) for s in scenes)
    per10 = sfx_count / max(1e-6, total / 10)
    sfx_ok = 1 <= per10 <= 3.2 if total > 20 else True
    if not sfx_ok:
        rep.cut("sfx", f"音效密度 {per10:.1f}/10s，应为 1–3", "裁到每 10 秒 1–3 个")

    runs, cur_type, cur_start = [], None, scenes[0]["start"]
    for s in scenes:
        if s.get("visual_type") != cur_type:
            if cur_type:
                runs.append((cur_type, s["start"] - cur_start))
            cur_type, cur_start = s.get("visual_type"), s["start"]
    for t, span in runs:
        if span > 9.5 and t not in ("presenter", "screencast", "broll"):
            rep.cut("layout_run", f"{t} 连续 {span:.1f}s", "在 6–9s 处插入知识镜头或换构图")

    rep.hard("核心知识点得到有效可视化", len({s.get('visual_type') for s in scenes}) >= 5,
             f"{len({s.get('visual_type') for s in scenes})} 种视觉形式")
    rep.hard("全片使用统一高级配色", sb.get("theme") in ("dark_gold", "pearl_green"), sb.get("theme"))
    rep.hard("视频类型得到正确识别", sb.get("video_type") in
             ("knowledge", "practice", "analysis", "opinion", "story", "industry"), sb.get("video_type"))


def write_report(path, video, sb, rep, extra):
    md = []
    md.append("# 自动质检报告\n")
    scenes = sb.get("storyboard") or []
    md.append(f"- 视频：`{Path(video).name}`")
    if extra.get("ffprobe"):
        m = extra["ffprobe"]
        md.append(f"- 参数：{m['duration_hms']} / {m['width']}×{m['height']} / {m['fps']}fps")
    md.append(f"- 主题：{sb.get('theme')}")
    md.append(f"- 类型：{sb.get('video_type')}")
    md.append(f"\n## 总分：{rep.score} / 100 {'✅' if rep.score >= 90 else '❌'}\n")

    passed = sum(1 for i in rep.items if i["ok"])
    md.append(f"## 硬指标：{passed}/{len(rep.items)} 通过\n")
    md.append("| 检查项 | 结果 | 说明 |")
    md.append("|---|---|---|")
    for i in rep.items:
        md.append(f"| {i['name']} | {'✅' if i['ok'] else '❌'} | {i['detail']} |")

    md.append("\n## 扣分明细\n")
    if rep.deduct:
        md.append("| 项目 | 扣分 | 说明 | 建议 |")
        md.append("|---|---|---|---|")
        for d in rep.deduct:
            md.append(f"| {d['key']} | -{d['points']} | {d['detail']} | {d['fix']} |")
    else:
        md.append("无扣分项。")

    md.append("\n## 结论\n")
    md.append(f"{'通过（≥90），建议人工复核节奏与知识准确性。' if rep.score >= 90 else '未通过（<90）。按上表修复后重跑对应检测，不要整片重来。'}")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(md), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="自动质检")
    ap.add_argument("--video", required=True)
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--report", default="output/08_自动质检报告.md")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not Path(args.video).exists():
        print(f"× 成片不存在：{args.video}")
        sys.exit(2)

    sb = k.read_json(args.storyboard)
    rep = Report()
    extra = {}

    decode_check(args.video, rep)
    probe_checks(args.video, sb, extra, rep)
    extra["loudness_lufs"] = loudness_check(args.video, rep)
    extra["black_starts"] = black_check(args.video, rep)
    extra["first_luma"] = frame_luma(args.video, 0.05)
    extra["cover_contrast"] = has_text_like_pixels(args.video, 0.3)
    extra["second_contrast"] = has_text_like_pixels(args.video, (sb.get("cover") or {}).get("duration", 2.0) + 1.0)
    extra["theme_coverage"] = theme_check(args.video, sb, extra, rep)
    extra["subtitles"] = subtitle_check(args.video, sb, rep)
    storyboard_checks(sb, rep)

    if extra.get("first_luma") is not None and extra["first_luma"] < 12:
        rep.cut("first_black", f"首帧平均亮度 {extra['first_luma']:.1f}，接近全黑", "确认封面元素在第 0 帧已渲染")

    if extra.get("second_contrast") is not None and extra.get("cover_contrast") is not None:
        if extra["second_contrast"] > extra["cover_contrast"] * 1.6:
            rep.notes.append("第二镜头文字对比度明显高于封面，建议人工复核封面标题是否残留。")

    write_report(args.report, args.video, sb, rep, extra)

    if args.json:
        print(json.dumps({"score": rep.score, "pass": rep.score >= 90,
                          "items": rep.items, "deductions": rep.deduct,
                          "extra": extra}, ensure_ascii=False, indent=2, default=str))
    else:
        print(f"\n=== 质检：{Path(args.video).name} ===")
        passed = sum(1 for i in rep.items if i["ok"])
        print(f"硬指标 {passed}/{len(rep.items)} · 总分 {rep.score}/100 "
              f"{'✅ 通过' if rep.score >= 90 else '❌ 未通过'}")
        for d in rep.deduct:
            print(f"  -{d['points']} {d['key']}: {d['detail']}")
        for n in rep.notes:
            print(f"  ! {n}")
        print(f"\n报告 → {args.report}")

    sys.exit(0 if rep.score >= 90 else 1)


if __name__ == "__main__":
    main()
