#!/usr/bin/env python3
"""check_environment.py · 环境自检

检查 ffmpeg / ffprobe / 转写引擎 / Node+Remotion / 字体 / 磁盘，
输出人类可读报告或 JSON。缺关键项时以非零码退出（提示"别硬跑"）。

用法：
    python3 scripts/check_environment.py
    python3 scripts/check_environment.py --json --out work/env_report.json
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kve_common as k


CRITICAL = ("ffmpeg", "ffprobe")
RECOMMENDED = ("python3", "node", "npx")


def check_binaries():
    bins = k.which_all(CRITICAL + RECOMMENDED + ("git",))
    return {name: {"found": bool(path), "path": path} for name, path in bins.items()}


def check_python_pkgs():
    pkgs = {}
    for mod, label in [
        ("faster_whisper", "faster-whisper"),
        ("whisper", "openai-whisper"),
        ("fontTools", "fonttools"),
        ("PIL", "pillow"),
        ("jsonschema", "jsonschema"),
    ]:
        try:
            __import__(mod)
            pkgs[label] = True
        except Exception:
            pkgs[label] = False
    return pkgs


def check_transcribe_engine(pkgs):
    if pkgs.get("faster-whisper"):
        return {"engine": "faster-whisper", "available": True}
    if pkgs.get("openai-whisper"):
        return {"engine": "openai-whisper", "available": True}
    for name in ("whisper-cli", "whisper", "whisper.cpp"):
        if shutil.which(name):
            return {"engine": name, "available": True}
    return {"engine": None, "available": False,
            "hint": "pip install faster-whisper，或安装 whisper.cpp，或改用宿主模型转写"}


def check_renderer():
    node = shutil.which("node")
    npx = shutil.which("npx")
    remotion_ok = False
    if node and npx:
        pkg = k.ROOT / "templates" / "remotion" / "package.json"
        node_modules = k.ROOT / "templates" / "remotion" / "node_modules"
        remotion_ok = pkg.exists() and node_modules.exists()
    return {"node": bool(node), "npx": bool(npx), "remotion_installed": remotion_ok,
            "hint": None if remotion_ok else "cd templates/remotion && npm install"}


def check_fonts():
    dirs = ["/usr/share/fonts", "/usr/local/share/fonts", str(Path.home() / ".fonts"),
            str(k.ROOT / "assets" / "fonts")]
    found = []
    for d in dirs:
        p = Path(d)
        if not p.exists():
            continue
        for f in p.rglob("*"):
            if f.suffix.lower() in (".ttf", ".otf", ".ttc"):
                found.append(f.name)
    cjk = [f for f in found if any(key in f.lower() for key in
            ("noto", "sourcehan", "source-han", "pingfang", "songti", "heiti", "alibaba", "siyuan"))]
    return {"total": len(found), "cjk_candidates": cjk[:10],
            "ok": bool(cjk), "hint": None if cjk else "把中文字体放入 assets/fonts/"}


def check_disk(path="."):
    try:
        usage = shutil.disk_usage(path)
        return {"free_gb": round(usage.free / 1024 ** 3, 1),
                "ok": usage.free > 2 * 1024 ** 3}
    except Exception as e:
        return {"error": str(e), "ok": False}


def main():
    ap = argparse.ArgumentParser(description="Knowledge Video Editor 环境自检")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--out", help="把报告写到文件")
    args = ap.parse_args()

    pkgs = check_python_pkgs()
    report = {
        "binaries": check_binaries(),
        "python_packages": pkgs,
        "transcribe": check_transcribe_engine(pkgs),
        "renderer": check_renderer(),
        "fonts": check_fonts(),
        "disk": check_disk(),
        "configs": {n: (k.CONFIG_DIR / f"{n}.json").exists()
                    for n in ("default", "dark-gold", "pearl-green", "horizontal",
                              "vertical", "safe-areas", "glossary", "storyboard.schema")},
    }

    blockers = []
    for name in CRITICAL:
        if not report["binaries"].get(name, {}).get("found"):
            blockers.append(f"缺少 {name}（必需）")
    if not report["transcribe"]["available"]:
        blockers.append("无本地转写引擎（需宿主模型替代，否则不可出片）")
    if not all(report["configs"].values()):
        blockers.append("config 目录不完整")
    if not report["disk"].get("ok"):
        blockers.append("磁盘剩余 < 2GB")

    warnings = []
    if not report["renderer"]["remotion_installed"]:
        warnings.append("Remotion 未安装，无法渲染可视化合成")
    if not report["fonts"]["ok"]:
        warnings.append("未找到中文字体，字幕会方框")

    report["blockers"] = blockers
    report["warnings"] = warnings
    report["ready"] = not blockers

    if args.out:
        k.write_json(args.out, report)

    if args.json:
        print(k.json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("\n=== Knowledge Video Editor · 环境自检 ===\n")
        print("二进制：")
        for n, v in report["binaries"].items():
            print(f"  {'✓' if v['found'] else '×'} {n:<10} {v['path'] or ''}")
        print(f"\n转写引擎：{report['transcribe']['engine'] or '无'}")
        print(f"渲染器：node={report['renderer']['node']} remotion={report['renderer']['remotion_installed']}")
        print(f"字体：{report['fonts']['total']} 个，中文候选 {len(report['fonts']['cjk_candidates'])} 个")
        print(f"磁盘：剩余 {report['disk'].get('free_gb')} GB")
        if blockers:
            print("\n阻塞项（必须先解决）：")
            for b in blockers:
                print(f"  × {b}")
        if warnings:
            print("\n警告（可降级）：")
            for w in warnings:
                print(f"  ! {w}")
        print(f"\n结论：{'可以开工' if report['ready'] else '不能开工'}")

    sys.exit(0 if report["ready"] else 1)


if __name__ == "__main__":
    main()
