#!/usr/bin/env python3
"""validate_storyboard.py · 分镜校验（不通过不许渲染）

逐条检查硬规则：
  - 字段齐全、类型正确
  - 封面 ≤2 行、每行 ≤4 字、visible_from_first_frame=true
  - 第二镜头起 cover_visible 不为 true
  - 横屏导航 3–6 章、每章 2–6 字、height_ratio ≤ 0.08
  - scene 时间连续、无重叠、无空洞
  - 每个 scene 有 animation_plan、visual_type 合法
  - 每秒有安排（覆盖率）
  - 单一构图连续 ≤ 9s
  - 双语字幕配置与安全区开关

用法：
    python3 scripts/validate_storyboard.py --storyboard work/storyboard.json
    python3 scripts/validate_storyboard.py --storyboard work/storyboard.json --fix-suggest
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kve_common as k

VALID_VISUALS = {
    "cover", "presenter", "presenter_pip", "keyword", "flow_steps", "mindmap", "compare",
    "chart", "org_tree", "timeline", "screencast", "map", "icon_story", "cards", "citation",
    "simulation", "broll", "whiteboard", "number_roll", "causal_chain", "summary",
}

CJK_OR_WORD = re.compile(r"[\u4e00-\u9fff]|[A-Za-z0-9]+")


def visual_width_units(s: str) -> int:
    """按"汉字=1，字母数字串=1"计算视觉字数，用于封面 4 字限制。"""
    units, i = 0, 0
    while i < len(s):
        ch = s[i]
        if "\u4e00" <= ch <= "\u9fff":
            units += 1
            i += 1
        elif ch.isalnum():
            j = i
            while j < len(s) and s[j].isalnum():
                j += 1
            units += 1
            i = j
        elif ch in "，。、；：（）\"'“”‘’·":
            i += 1
        else:
            i += 1
    return units


class Result:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, code, msg, fix=None):
        self.errors.append({"code": code, "msg": msg, "fix": fix})

    def warn(self, code, msg, fix=None):
        self.warnings.append({"code": code, "msg": msg, "fix": fix})

    @property
    def ok(self):
        return not self.errors


def check_cover(sb, r: Result):
    cover = sb.get("cover") or {}
    lines = cover.get("lines") or []
    if not lines:
        r.err("COVER_EMPTY", "封面没有标题", "cover.lines 至少 1 行")
        return
    if len(lines) > 2:
        r.err("COVER_LINES", f"封面 {len(lines)} 行，超过 2 行", "合并为 2 行")
    for i, ln in enumerate(lines):
        u = visual_width_units(ln)
        if u > 4:
            r.err("COVER_CHARS", f"第 {i+1} 行「{ln}」占 {u} 字宽，超过 4",
                  f"压缩到 4 字以内，如「{ln[:3]}」")
    if not cover.get("visible_from_first_frame"):
        r.err("COVER_FIRST_FRAME", "cover.visible_from_first_frame 必须为 true（第一帧即封面）")
    dur = cover.get("duration", 2.0)
    if not (0.5 <= dur <= 4):
        r.warn("COVER_DUR", f"封面时长 {dur}s 超出 0.5–4s 建议区间", "改为 1.5–2s")


def check_nav(sb, r: Result):
    nav = sb.get("navigation") or {}
    ratio = sb.get("aspect_ratio")
    chapters = nav.get("chapters") or []
    if ratio == "16:9" and not nav.get("enabled"):
        r.err("NAV_MISSING", "横屏视频必须启用动态章节导航", "navigation.enabled=true")
    if nav.get("enabled"):
        if not (3 <= len(chapters) <= 6):
            r.err("NAV_COUNT", f"章节 {len(chapters)} 个，应为 3–6 个", "合并或拆分章节")
        for c in chapters:
            if not (2 <= visual_width_units(c) <= 6):
                r.err("NAV_NAME", f"章节名「{c}」应为 2–6 字", "改成动宾短语，如「逻辑」")
        hr = nav.get("height_ratio", 0.06)
        if hr > 0.08:
            r.err("NAV_HEIGHT", f"导航栏占高 {k.pct(hr)}%，超过 8%", "height_ratio ≤ 0.08")
    if not nav.get("hide_during_cover", True):
        r.err("NAV_COVER", "封面期间必须隐藏导航栏", "hide_during_cover=true")


def check_scenes(sb, r: Result):
    scenes = sb.get("storyboard") or []
    if not scenes:
        r.err("SCENES_EMPTY", "storyboard 为空")
        return
    cover_dur = (sb.get("cover") or {}).get("duration", 2.0)
    prev_end = None
    for i, sc in enumerate(scenes):
        sid = sc.get("scene_id", f"#{i+1}")
        for fld in ("scene_id", "start", "end", "visual_type"):
            if fld not in sc:
                r.err("SCENE_FIELD", f"{sid} 缺少 {fld}")
        st, en = sc.get("start", 0), sc.get("end", 0)
        if en <= st:
            r.err("SCENE_TIME", f"{sid} 结束 {en} 不晚于开始 {st}")
        if prev_end is not None:
            if abs(st - prev_end) > 0.05:
                gap = st - prev_end
                if gap > 0:
                    r.err("SCENE_GAP", f"{sid} 与上一镜头之间有 {gap:.2f}s 空洞", f"start 改为 {prev_end}")
                else:
                    r.err("SCENE_OVERLAP", f"{sid} 与上一镜头重叠 {-gap:.2f}s", f"start 改为 {prev_end}")
        prev_end = en

        vt = sc.get("visual_type")
        if vt not in VALID_VISUALS:
            r.err("SCENE_TYPE", f"{sid} visual_type「{vt}」不合法", f"取值见 {sorted(VALID_VISUALS)}")

        if i == 0 and vt != "cover":
            r.err("SCENE_NO_COVER", "第一个镜头必须是 cover")
        if i > 0 and st >= cover_dur - 0.01:
            if sc.get("cover_visible") is True:
                r.err("COVER_LEAK", f"{sid} 在封面结束后仍显示封面标题", "cover_visible=false")
        if i > 0 and vt == "cover":
            r.err("COVER_DUP", f"{sid} 第二个 cover 镜头，封面只允许出现一次")

        if not sc.get("animation_plan"):
            r.err("SCENE_NO_ANIM", f"{sid} 没有 animation_plan（每秒必须有安排）",
                  "至少补一条 read_hold 或节点出现")
        else:
            for a in sc["animation_plan"]:
                if "time" not in a or "action" not in a:
                    r.err("ANIM_FIELD", f"{sid} animation_plan 项缺 time/action")
                elif not (st - 0.01 <= a["time"] <= en + 0.01):
                    r.err("ANIM_RANGE", f"{sid} 动画时间 {a['time']} 不在镜头区间 [{st},{en}]")

        if sc.get("chapter") and sb.get("navigation", {}).get("enabled"):
            if sc["chapter"] not in (sb["navigation"].get("chapters") or []):
                r.err("SCENE_CHAPTER", f"{sid} chapter「{sc['chapter']}」不在导航章节列表里")

    # 覆盖率：每秒是否有安排
    total = scenes[-1]["end"] - scenes[0]["start"]
    covered = 0.0
    for sc in scenes:
        times = {round(a["time"], 1) for a in sc.get("animation_plan", []) if "time" in a}
        covered += max(0.0, min(sc["end"], (max(times) + 1.5) if times else sc["start"] + 1) - sc["start"])
    cov = covered / total if total else 0
    if cov < 0.85:
        r.warn("ANIM_COVERAGE", f"动态/阅读安排覆盖率 {k.pct(cov)}%，低于 85%", "给空白段补 read_hold 或强调")

    # 单一构图连续
    run_start, run_type = scenes[0]["start"], scenes[0].get("visual_type")
    for sc in scenes[1:] + [{"start": scenes[-1]["end"], "visual_type": None}]:
        if sc.get("visual_type") != run_type:
            span = sc["start"] - run_start
            if span > 9.5 and run_type not in ("presenter", "screencast"):
                r.warn("LAYOUT_RUN", f"{run_type} 连续 {span:.1f}s 未换构图（建议 ≤9s）", "插入知识镜头或换构图")
            run_start, run_type = sc["start"], sc.get("visual_type")


def check_subs(sb, r: Result):
    subs = sb.get("subtitles") or {}
    langs = subs.get("languages") or []
    if subs.get("layout") != "chinese_above_english":
        r.err("SUB_LAYOUT", "字幕必须先中后英", "layout=chinese_above_english")
    if "zh" not in langs:
        r.warn("SUB_ZH", "没有中文字幕")
    if "en" not in langs:
        r.warn("SUB_EN", "没有英文字幕，双语要求未满足")
    if not subs.get("safe_area_check"):
        r.warn("SUB_SAFE", "未开启安全区校验", "safe_area_check=true")


def check_theme(sb, r: Result):
    if sb.get("theme") not in ("dark_gold", "pearl_green"):
        r.err("THEME", f"theme「{sb.get('theme')}」不合法", "dark_gold / pearl_green")


def check_ratio(sb, r: Result):
    ratio, res = sb.get("aspect_ratio"), sb.get("resolution") or []
    if ratio == "16:9" and res != [1920, 1080]:
        if len(res) == 2 and abs(res[0] / res[1] - 16 / 9) > 0.02:
            r.err("RES", f"{ratio} 的分辨率 {res} 不匹配", "[1920,1080]")
    if ratio == "9:16" and len(res) == 2 and abs(res[0] / res[1] - 9 / 16) > 0.02:
        r.err("RES", f"{ratio} 的分辨率 {res} 不匹配", "[1080,1920]")
    if ratio not in ("16:9", "9:16", "1:1", "4:3", "3:4"):
        r.err("RATIO", f"aspect_ratio「{ratio}」不支持")


def main():
    ap = argparse.ArgumentParser(description="分镜校验")
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fix-suggest", action="store_true")
    args = ap.parse_args()

    sb = k.read_json(args.storyboard)
    r = Result()

    for fld in ("video_type", "aspect_ratio", "resolution", "theme", "cover", "navigation", "subtitles", "storyboard"):
        if fld not in sb:
            r.err("MISSING_FIELD", f"缺少顶层字段 {fld}")
    if r.errors:
        pass
    else:
        check_ratio(sb, r)
        check_theme(sb, r)
        check_cover(sb, r)
        check_nav(sb, r)
        check_subs(sb, r)
        check_scenes(sb, r)

    if args.json:
        print(json.dumps({"ok": r.ok, "errors": r.errors, "warnings": r.warnings},
                         ensure_ascii=False, indent=2))
    else:
        print(f"\n=== 分镜校验：{args.storyboard} ===")
        if r.ok:
            print("✓ 硬规则全部通过")
        else:
            print(f"× {len(r.errors)} 项不合格：")
            for e in r.errors:
                print(f"  [{e['code']}] {e['msg']}")
                if args.fix_suggest and e.get("fix"):
                    print(f"        → {e['fix']}")
        if r.warnings:
            print(f"\n! {len(r.warnings)} 项提示：")
            for w in r.warnings:
                print(f"  [{w['code']}] {w['msg']}")
                if args.fix_suggest and w.get("fix"):
                    print(f"        → {w['fix']}")
        print(f"\n结论：{'可进入渲染' if r.ok else '禁止渲染，先修上面 × 项'}")

    sys.exit(0 if r.ok else 1)


if __name__ == "__main__":
    main()
