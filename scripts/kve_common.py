#!/usr/bin/env python3
"""kve_common.py · Knowledge Video Editor 公共工具层

所有脚本共享：配置加载、JSON 读写、ffmpeg 调用、日志、时间格式化。
不引入第三方依赖（可选依赖在调用处按需 import）。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"


# ---------------------------------------------------------------- 配置
def load_config(name: str) -> dict:
    """读取 config/<name>.json，找不到时给出明确错误而不是静默返回空。"""
    path = CONFIG_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"缺少配置：{path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def default_cfg() -> dict:
    return load_config("default")["defaults"]


def theme_cfg(theme: str) -> dict:
    mapping = {"dark_gold": "dark-gold", "pearl_green": "pearl-green"}
    return load_config(mapping.get(theme, theme))


def ratio_cfg(ratio: str) -> dict:
    return load_config("horizontal" if ratio == "16:9" else "vertical")


# ---------------------------------------------------------------- IO
def read_json(path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------- 进程
def which_all(names) -> dict:
    return {n: shutil.which(n) for n in names}


def run(cmd, check=False, timeout=600, cwd=None) -> subprocess.CompletedProcess:
    """执行命令并捕获输出。check=False 时由调用方判断返回码。"""
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, 124, "", f"timeout after {timeout}s")


def ffprobe_json(path: str) -> dict:
    r = run(["ffprobe", "-v", "error", "-print_format", "json",
             "-show_format", "-show_streams", str(path)])
    if r.returncode != 0:
        raise RuntimeError(f"ffprobe 失败：{r.stderr.strip()[:500]}")
    return json.loads(r.stdout)


# ---------------------------------------------------------------- 文本
def pct(v: float) -> int:
    return int(round(v * 100))


def fmt_time(t: float) -> str:
    t = max(0.0, float(t))
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    if h:
        return f"{h:02d}:{m:02d}:{s:05.2f}"
    return f"{m:02d}:{s:05.2f}"


def fmt_srt_time(t: float) -> str:
    ms = int(round((t - int(t)) * 1000))
    sec = int(t)
    return f"{sec//3600:02d}:{(sec%3600)//60:02d}:{sec%60:02d},{ms:03d}"


# ---------------------------------------------------------------- 日志
class Log:
    def __init__(self, quiet=False):
        self.quiet = quiet

    def __call__(self, msg: str, level="info"):
        if self.quiet and level == "info":
            return
        icon = {"info": "·", "ok": "✓", "warn": "!", "err": "×"}.get(level, "·")
        print(f"[{icon}] {msg}", file=sys.stderr, flush=True)

    def step(self, idx, total, msg):
        print(f"\n[{idx}/{total}] {msg}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------- 文件
def ensure_dir(path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
