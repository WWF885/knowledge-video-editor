# Knowledge Video Editor · 知识型口播智能剪辑

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](VERSION)

> 一段没剪过的口播视频进去，一条能直接发布的知识型成片出来。
> 让知识看得见，让逻辑更清晰，让观看不枯燥。

---

## 它解决什么问题

真人对着镜头讲 3 分钟知识，剪出来通常是这三种惨状：

- 全程大脸，观众 20 秒划走；
- 塞满花字，像劣质微商课；
- 剪成 PPT 朗读，节奏死掉。

本 Skill 的做法是：**先读懂内容，再决定怎么拍。**

它会自己判断这条视频是知识科普、工具实操、商业分析、观点表达、故事分享还是行业解读，然后按内容属性给每一段配不同的视觉策略 —— 该上图的上图，该让真人说话的让真人说话。

---

## 核心特性

| 特性 | 说明 |
|---|---|
| **自主识别类型** | 不要求用户选模板；整片 + 段落双层判断 |
| **横竖屏自适应** | 16:9 / 9:16 共用分析结果，分别重排布局重渲染，禁止裁切 |
| **动态章节导航** | 横屏顶部 3–6 章导航，随口播进度平滑推进，占高 ≤ 8% |
| **首帧即封面** | 第一帧就是完整封面，最多 2 行、每行 4 字，直接可发布 |
| **两套高级配色** | 深空黑金（科技/商业/AI）、珍珠墨绿（成长/认知/文旅/教育） |
| **20+ 视觉组件** | V01–V20，可组合、可扩展、可自建 |
| **逐秒分镜** | 每 1 秒有安排，每 3 秒评估构图，0.2–0.5 秒级动画 |
| **中英双语字幕** | 中文在上英文在下，逐句语义断句，字宽实测防溢出 |
| **自动精剪** | 去重复、去口误、压停顿、清语气词、降噪、响度归一 |
| **自动质检** | 15 项硬指标 + 百分制评分，< 90 自动定位修复 |

---

## 快速开始

```bash
# 0) 环境自检（先看有没有 ffmpeg / 转写 / 渲染）
python3 scripts/check_environment.py

# 1) 读视频
python3 scripts/analyze_video.py --video input.mp4 --out work/video_meta.json

# 2) 转写 + 双语
python3 scripts/transcribe.py --video input.mp4 --bilingual --out work/

# 3) 精剪（按 EDL）
python3 scripts/edit_video.py --video input.mp4 --edl work/edl.json --out work/edited.mp4

# 4) 校验分镜
python3 scripts/validate_storyboard.py --storyboard work/storyboard.json

# 5) 渲染（同时导出封面）
python3 scripts/render_video.py --storyboard work/storyboard.json --ratio 16:9 \
    --audio work/edited.mp4 --cover output/02_首帧封面.png --out output/01_最终成片.mp4

# 6) 质检
python3 scripts/quality_check.py --video output/01_最终成片.mp4 \
    --storyboard work/storyboard.json --report output/08_自动质检报告.md
```

一键跑完整流水线：

```bash
python3 scripts/run.py --video input.mp4 --out ./我的项目 --ratio 9:16 --theme pearl-green
```

---

## 环境依赖

| 能力 | 必需 | 说明 |
|---|---|---|
| ffmpeg / ffprobe | ✅ | 精剪、混音、抽帧、检测 |
| Python 3.9+ | ✅ | 脚本运行 |
| Node 18+ / Remotion | 渲染需要 | 可视化合成 |
| faster-whisper 或 openai-whisper | 转写需要 | 无则退化为宿主模型转写 |
| 中英字体（思源黑体 Heavy 等） | 渲染需要 | 见 `assets/fonts/README.md` |

---

## 目录

```
SKILL.md               规则总纲（Agent 入口）
AGENTS.md              执行协议
references/            10 份细则
config/                机器可读配置 + JSON Schema
scripts/               8 个脚本（分析/转写/剪辑/校验/渲染/质检/编排）
templates/remotion/    React 渲染引擎
examples/              4 类导演计划示例
```

---

## 设计哲学

1. **理解优先于模板。** 没有"万能模板"，只有"这段内容最适合的表达方式"。
2. **留白是高级感的来源。** 少特效、准层级、够留白，比堆转场有效十倍。
3. **可读性高于信息密度。** 单位时间塞太多，等于什么都没讲。
4. **程序做确定性的事，模型做判断性的事。** 像素交给代码，语义交给 AI。
5. **诚实优于完成度。** 出不来就说出不来，不交半成品。

---

## License

MIT © 2026 WWF885
