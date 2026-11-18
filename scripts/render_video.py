#!/usr/bin/env python3
"""render_video.py · 渲染合成（Remotion + ffmpeg 混音）

职责：
  1. 把 storyboard.json + 主题 + 比例布局合并成渲染 props
  2. 调 Remotion 渲出无声画面
  3. 混入精剪原声 / BGM / 音效
  4. 单独导出首帧封面（与视频第 0 帧像素一致）

前置：templates/remotion 已 npm install，且 storyboard 已通过 validate_storyboard.py。

用法：
    python3 scripts/render_video.py --storyboard work/storyboard.json --ratio 16:9 \
        --audio work/edited.mp4 --out output/01_最终成片.mp4 --cover output/02_首帧封面.png
    python3 scripts/render_video.py --cover-only --storyboard work/storyboard.json --cover cover.png
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kve_common as k

REMOTION_DIR = k.ROOT / "templates" / "remotion"
ENTRY = REMOTION_DIR / "src" / "index.ts"


def build_props(sb: dict, ratio_override=None, subs_path=None) -> dict:
    ratio = ratio_override or sb.get("aspect_ratio", "16:9")
    theme = sb.get("theme", "dark_gold")
    layout = k.ratio_cfg(ratio)
    safe = k.load_config("safe-areas")
    theme_data = k.theme_cfg(theme)
    props = {
        "storyboard": sb,
        "theme": theme_data,
        "layout": layout,
        "safeAreas": safe["horizontal_16_9"] if ratio == "16:9" else safe["vertical_9_16"],
        "aspectRatio": ratio,
        "resolution": layout["resolution"],
        "fps": sb.get("fps", layout.get("fps", 30)),
    }
    if subs_path and Path(subs_path).exists():
        props["subtitles"] = k.read_json(subs_path)
    elif sb.get("subtitles", {}).get("source") and Path(sb["subtitles"]["source"]).exists():
        props["subtitles"] = k.read_json(sb["subtitles"]["source"])
    return props


def ensure_remotion(log):
    node = shutil.which("node")
    npx = shutil.which("npx")
    if not node or not npx:
        log("没有 node/npx，无法渲染画面。请安装 Node 18+ 并 cd templates/remotion && npm install", "err")
        return False
    if not (REMOTION_DIR / "node_modules").exists():
        log("Remotion 依赖未安装：cd templates/remotion && npm install", "err")
        return False
    return True



def _serve_dir(directory: Path):
    """起一个临时静态服务：Remotion 只能稳定地从 HTTP 或 public/ 读媒体。"""
    import http.server, socketserver, threading
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=str(directory), **kw)
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()
    return httpd, port


def render_still(props_path, out_png, log) -> bool:
    cmd = ["npx", "remotion", "still", "src/index.ts", "KnowledgeVideo", out_png,
           f"--props={props_path}", "--frame=0", "--log=error"]
    r = k.run(cmd, timeout=900, cwd=str(REMOTION_DIR))
    if r.returncode != 0:
        log(f"封面渲染失败：{r.stderr.strip()[-600:]}", "err")
        return False
    return True


def render_video(props_path, out_video, concurrency=4, log=None) -> bool:
    cmd = ["npx", "remotion", "render", "src/index.ts", "KnowledgeVideo", out_video,
           f"--props={props_path}", "--codec=h264", "--crf=18",
           f"--concurrency={concurrency}", "--log=error"]
    r = k.run(cmd, timeout=7200, cwd=str(REMOTION_DIR))
    if r.returncode != 0:
        (log or print)(f"Remotion 渲染失败：{r.stderr.strip()[-800:]}", "err")
        return False
    return True


def mux_audio(silent_video, audio_src, out_path, bgm=None, bgm_db=-22, target_lufs=-16, log=None) -> bool:
    log = log or (lambda *a, **kw: None)
    afilter = None
    if bgm and Path(bgm).exists():
        afilter = (f"[1:a]volume=1.0[v];[2:a]volume={10 ** (bgm_db / 20):.4f},highpass=120[b];"
                   f"[b][v]sidechaincompress=threshold=0.02:ratio=6:attack=15:release=300[duck];"
                   f"[v][duck]amix=inputs=2:weights=1 0.6:duration=first[lv];"
                   f"[lv]loudnorm=I={target_lufs}:TP=-1.5:LRA=11[a]")
        cmd = ["ffmpeg", "-y", "-i", silent_video, "-i", audio_src, "-i", bgm,
               "-filter_complex", afilter, "-map", "0:v", "-map", "[a]",
               "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out_path]
    else:
        cmd = ["ffmpeg", "-y", "-i", silent_video, "-i", audio_src,
               "-map", "0:v", "-map", "1:a", "-c:v", "copy",
               "-c:a", "aac", "-b:a", "192k", "-shortest",
               "-movflags", "+faststart", out_path]
    r = k.run(cmd, timeout=1800)
    if r.returncode != 0:
        log(f"混音失败：{r.stderr.strip()[-700:]}", "err")
        return False
    return True


def main():
    ap = argparse.ArgumentParser(description="渲染合成")
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--ratio", default=None, help="覆盖 storyboard 里的比例")
    ap.add_argument("--audio", help="精剪后的原声（混音源）")
    ap.add_argument("--presenter", help="真人素材路径，默认等于 --audio")
    ap.add_argument("--bgm", help="背景音乐路径")
    ap.add_argument("--bgm-db", type=float, default=-22)
    ap.add_argument("--subtitles", help="subtitle.json 路径，默认读 storyboard.subtitles.source")
    ap.add_argument("--out", default="output/01_最终成片.mp4")
    ap.add_argument("--cover", default="output/02_首帧封面.png")
    ap.add_argument("--cover-only", action="store_true")
    ap.add_argument("--silent-only", action="store_true", help="只渲画面不混音")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-validate", action="store_true")
    args = ap.parse_args()

    log = k.Log()
    sb = k.read_json(args.storyboard)

    if not args.skip_validate:
        r = k.run([sys.executable, str(k.ROOT / "scripts" / "validate_storyboard.py"),
                   "--storyboard", args.storyboard])
        if r.returncode != 0:
            print(r.stdout)
            log("分镜校验未通过，禁止渲染。先修 storyboard。", "err")
            sys.exit(3)
        log("分镜校验通过", "ok")

    props = build_props(sb, args.ratio, args.subtitles)
    # 精剪后的原声视频同时就是真人素材：分镜里的 presenter 镜头与圆形头像直接取它
    presenter = args.presenter or args.audio
    httpd = None
    if presenter and Path(presenter).exists():
        src_path = Path(presenter).resolve()
        httpd, port = _serve_dir(src_path.parent)
        props["presenterVideo"] = f"http://127.0.0.1:{port}/{src_path.name}"
        props["presenterLocalPath"] = str(src_path)
        # 头像取景需要真实宽高比，否则圆内会裁掉额头/肩膀
        try:
            pm = k.probe(src_path)
            if pm.get("width") and pm.get("height"):
                props["presenterAspect"] = round(pm["width"] / pm["height"], 4)
        except Exception:
            pass
    work = k.ensure_dir(Path(args.out).parent / "work" if Path(args.out).parent != Path(".") else "work")
    props_path = Path(work) / "render_props.json"
    if not props_path.is_absolute():
        props_path = props_path.resolve()
    k.write_json(props_path, props)
    log(f"props → {props_path}（主题 {props['theme']['id']}，"
        f"{props['resolution'][0]}×{props['resolution'][1]}，{len(sb.get('storyboard', []))} 镜头）")

    if args.dry_run:
        print(f"props: {props_path}\nremotion render src/index.ts KnowledgeVideo {args.out}")
        return

    if not ensure_remotion(log):
        sys.exit(4)

    out_dir = k.ensure_dir(Path(args.out).parent)
    if args.cover:
        k.ensure_dir(Path(args.cover).parent)
        if render_still(str(props_path), str(Path(args.cover).resolve()), log):
            log(f"首帧封面 → {args.cover}", "ok")

    if args.cover_only:
        if httpd: httpd.shutdown()
        return

    silent = Path(out_dir) / "_silent.mp4"
    if not render_video(str(props_path), str(silent), log=log):
        sys.exit(5)
    log(f"画面渲完 → {silent}", "ok")

    if httpd: httpd.shutdown()
    if args.silent_only or not args.audio:
        if args.audio is None:
            log("未提供 --audio，交付无声画面（不合格，需补音）", "warn")
        shutil.move(str(silent), args.out)
    else:
        if not Path(args.audio).exists():
            log(f"原声文件不存在：{args.audio}", "err")
            sys.exit(6)
        cfg = k.default_cfg()
        if not mux_audio(str(silent), args.audio, args.out, args.bgm, args.bgm_db,
                         cfg["audio"]["target_lufs"], log):
            sys.exit(7)
        silent.unlink(missing_ok=True)
        log(f"混音完成 → {args.out}", "ok")

    meta = k.probe(args.out)
    k.write_json(Path(out_dir) / "render_meta.json", meta)
    print(f"\n成片 {args.out}\n{meta['width']}×{meta['height']} · {meta['duration_hms']} · "
          f"{meta['fps']}fps · {meta['size_mb']}MB")


if __name__ == "__main__":
    main()
