---
name: knowledge-video-editor
description: 知识型口播智能剪辑（Knowledge Video Editor）。当用户上传或指定一段未剪辑的真人/数字人口播视频，要求做自动精剪、知识可视化包装、加中英双语字幕、生成封面帧、输出横屏 16:9 或竖屏 9:16 成片时使用。适用于知识科普、工具实操、商业分析、观点表达、故事分享、行业解读六类内容，内置 21 种视觉组件、两套高级配色（深空黑金 / 珍珠墨绿）、动态章节导航栏、真人圆形头像与自动质检。也适用于要求"帮我剪口播视频""把口播做成知识视频""视频剪辑自动化""批量剪辑""生成封面首帧"等场景。
version: 1.0.1
license: MIT
---

# Knowledge Video Editor · 知识型口播智能剪辑

> 让知识看得见，让逻辑更清晰，让观看不枯燥。

本 Skill 把"一段未经剪辑的口播视频"变成"可直接发布的知识型成片"。你只要给它视频，它自己完成：读懂内容 → 判断类型 → 精剪原声 → 导演策划 → 逻辑可视化 → 双语字幕 → 首帧封面 → 质量验收 → 出片交付。

**核心主张：默认全自动，不需要用户逐步确认；但绝不伪造成片。**

---

## 一、先判断：这件事该不该用本 Skill

| 该用 | 不该用 |
|---|---|
| 真人/数字人口播视频（对着镜头讲知识、讲方法、讲观点） | 纯 Vlog、旅行随手拍（无讲解主线） |
| 已有口播 + 需要重新包装成知识视频 | 纯影视剪辑、剧情片、短剧 |
| 需要横屏/竖屏成片、双语字幕、封面首帧 | 只需要转码、裁剪、改分辨率 |
| 批量标准化出片（同一套视觉规范） | 需要保留原样只做字幕压制（用基础字幕流程即可） |

判断依据：**视频里有没有"能被结构化讲解的信息"**。有，就进本 Skill。

---

## 二、开工前的三条铁律

1. **先看环境，再动手。** 执行 `python3 scripts/check_environment.py --json`，确认 ffmpeg / 转写引擎 / 渲染引擎 / 字体是否齐备。缺关键能力就报告实际缺口，不允许"假装出片"。
2. **先出计划，再渲染。** 必须先生成 `director_plan.json` 与 `storyboard.json`（逐秒分镜），通过 `validate_storyboard.py` 校验后才能进入渲染。
3. **原片不动。** 所有中间产物落在 `<project>/work/`，成片落在 `<project>/output/`。永远不要覆盖用户原视频。

---

## 三、13 步执行流水线

| 步骤 | 动作 | 产出 | 脚本 |
|---|---|---|---|
| 1 | 环境自检 | `env_report.json` | `check_environment.py` |
| 2 | 视频属性识别（横竖屏/时长/清晰度/帧率/人像位置） | `video_meta.json` | `analyze_video.py` |
| 3 | 内容理解与分段（判断整片类型 + 每段属性） | `analysis.json` | `analyze_video.py --content` 或宿主大模型 |
| 4 | 语音转写 + 精剪决策（重复/口误/停顿/语气词/首尾） | `transcript.json` + `edl.json` | `transcribe.py` |
| 5 | 精剪执行（裁切 + 降噪 + 响度归一 + 时间轴重映射） | `edited.mp4` + `timemap.json` | `edit_video.py` |
| 6 | 全片导演计划（视频类型/主题/封面/章节/节奏） | `director_plan.json` | 大模型 + 模板 |
| 7 | 逻辑可视化（知识点 → 视觉组件映射） | `visual_map.json` | 大模型 + `07` 规范 |
| 8 | 逐秒分镜（每 1 秒都有安排，每 3 秒评估构图） | `storyboard.json` | 大模型 + `storyboard.schema.json` |
| 9 | 自适应构图（横屏/竖屏安全区、真人头像区域） | `layout.json` | `config/safe-areas.json` |
| 10 | 中英双语字幕（逐句、语义断句、宽度实测） | `subtitle.srt` + `subtitle.json` | `transcribe.py --bilingual` |
| 11 | 首帧封面生成（第一帧即封面） | `cover.png` | `render_video.py --cover-only` |
| 12 | 正式渲染（Remotion 合成 + 真人头像 + 音效/BGM 混音） | `output/01_最终成片.mp4` | `render_video.py` |
| 13 | 质检与自动修复（内容/画面/字幕/声音/解码） | `qc_report.md` | `quality_check.py` |

一键串联：`python3 scripts/run.py --video <原片> --out <目录> --ratio 16:9`

---

## 四、不可违反的硬规则（违反即返工）

1. **第一帧必须是完整封面。** 不允许黑屏、空白、标题还在入场动画中。标题最多 **2 行**，每行最多 **4 字**（字母数字同样计数），总计 ≤ 8 字，位于视觉中心，特粗黑体大字。
2. **第二镜头起封面标题必须完全消失。** 封面默认停留 1.5–2 秒，与口播同步开始，不插入无声等待。
3. **横屏必须配动态章节导航栏。** 3–6 个章节，每章 2–6 字，随口播进度平滑切换，最多占画面高度 8%，封面期间隐藏。
4. **全片只用一个主色体系。** 深空黑金 或 珍珠墨绿，二选一，不许混搭。
5. **双语字幕中文在上、英文在下**，逐句同步，必须实测字宽，不许溢出、不许遮挡核心知识区、不许无限缩小字号。
6. **声音优先级：原人声 > 重点音效 > BGM。** BGM 必须低音量并随人声避让。
7. **不许为缩短时长删掉关键论据**，不许改变原始观点，不许改写事实。
8. **不许把横屏成片直接裁剪成竖屏**，必须重新布局、重新渲染。
9. **验收分 < 90 必须自动定位并修复**，修不好就如实报告，不许宣布合格。
10. **素材必须可授权使用**，不明来源的图片/音乐/视频一律不用。
11. **每个画面都必须有真人。** 真人镜头用 V01/V02 占满；知识画面（关键词、流程、对比、卡片、数字、总结等）**必须**在右上角叠加 V21 真人圆形头像，任何镜头都不允许全程无真人。
12. **圆形头像取景与位置三条铁律。**（a）圆内必须露出**头发 + 完整五官 + 上肩**，禁止裁掉额头或下巴；（b）固定**右上角**，竖屏压在导航条之下、横屏压在顶部右侧，与边缘留 48–52px；（c）**绝不能压住标题、知识卡片和字幕**——内容区要为它让位（竖屏内容整体下移、横屏右侧留 344px 安全区）。
13. **讲解文字默认放大 12%。** 知识画面的标题、要点、卡片正文统一按 `text_scale 1.12` 渲染，宁可减少字数，不要缩小字号。

---

## 五、视频类型判断（不是用户选，是你判断）

先判整片，再判段落。同一条视频里可以混用策略。

| 类型 | 优先剪辑方式 | 真人占比参考 |
|---|---|---|
| `knowledge` 知识科普 | 流程图、结构图、动态白板 | 20–35% |
| `practice` 工具实操 | 录屏、局部放大、操作演示 | 15–30% |
| `analysis` 商业分析 | 数据图、对比图、因果链 | 25–40% |
| `opinion` 观点表达 | 真人 + 关键词 + 案例 | 40–60% |
| `story` 故事分享 | 真人叙事 + 场景 + 时间轴 | 45–65% |
| `industry` 行业解读 | 地图、资料引用、实景、图表 | 25–45% |

> 比例是参考不是考勤。判断错类型 = 整片风格错，这一步决定后面 80% 的工作量。

---

## 六、目录结构

```
knowledge-video-editor/
├── SKILL.md                 # 本文件：唯一入口，规则总纲
├── AGENTS.md                # 给各 Agent 的执行协议（Codex/Claude/Gemini/豆包工作等）
├── README.md                # 人读版说明与效果展示
├── VERSION
├── references/              # 10 份细则（规则层，不含代码）
├── config/                  # 机器可读配置（主题/比例/安全区/术语表/Schema）
├── scripts/                 # 8 个可执行脚本（分析→剪辑→校验→渲染→质检）
├── templates/remotion/      # 可视化渲染引擎（React 组件）
├── assets/                  # 字体/图标/音乐/音效（授权素材，仓库内留空说明）
└── examples/                # 4 类真实导演计划示例
```

---

## 七、目录细则索引（按需精读，不要一次全吞）

| 需要解决 | 去读 |
|---|---|
| 怎么判断类型、怎么分段 | `references/01_视频理解与类型判断.md` |
| 删哪些、留哪些、怎么不删错 | `references/02_自动精细剪辑.md` |
| 封面怎么做才不返工 | `references/03_首帧封面规范.md` |
| 横竖屏布局、导航栏参数 | `references/04_横竖屏与动态导航.md` |
| 两个主题的色值与使用场景 | `references/05_配色与视觉设计.md` |
| 逐秒分镜怎么写、动画曲线 | `references/06_智能分镜与逐秒动态.md` |
| V01–V20 组件怎么选、V21 头像怎么做 | `references/07_视觉组件使用规范.md` |
| 字幕字号、断句、安全区 | `references/08_中英字幕与安全区.md` |
| BGM 与音效密度、避让 | `references/09_背景音乐与音效.md` |
| 质检 100 分怎么打、怎么修 | `references/10_质检与自动修复.md` |

---

## 八、命令行速查

```bash
# 1. 环境自检
python3 scripts/check_environment.py --json

# 2. 读取视频属性
python3 scripts/analyze_video.py --video input.mp4 --out work/video_meta.json

# 3. 转写（中英双语）
python3 scripts/transcribe.py --video work/edited.mp4 --bilingual --out work/

# 4. 按 EDL 精剪
python3 scripts/edit_video.py --video input.mp4 --edl work/edl.json --out work/edited.mp4

# 5. 校验分镜（不通过不许渲染）
python3 scripts/validate_storyboard.py --storyboard work/storyboard.json

# 6. 渲染（含封面单独导出，含真人圆形头像）
python3 scripts/render_video.py --storyboard work/storyboard.json --ratio 16:9 \
  --audio work/edited.mp4 --cover cover.png --out output/01_最终成片.mp4

# 7. 质检
python3 scripts/quality_check.py --video output/01_最终成片.mp4 \
  --storyboard work/storyboard.json --report output/08_自动质检报告.md

# 8. 全流程
python3 scripts/run.py --video input.mp4 --out project/ --ratio 9:16 --theme pearl-green
```

任何脚本都支持 `--dry-run`，先看它打算干什么。

---

## 九、数据结构（必须遵守的契约）

导演计划与分镜采用统一 JSON 契约：`config/storyboard.schema.json`。最小可用结构：

```json
{
  "video_type": "knowledge",
  "aspect_ratio": "16:9",
  "resolution": [1920, 1080],
  "theme": "dark_gold",
  "cover": {
    "lines": ["工作方式", "彻底变了"],
    "position": "center",
    "visible_from_first_frame": true,
    "duration": 2
  },
  "presenter": {
    "always_visible": true,
    "badge": { "enabled": true, "diameter_px": 192, "top_px": 312, "focus_x": 0.62, "focus_y": 0.34, "zoom": 1.0 }
  },
  "navigation": { "enabled": true, "chapters": ["现状", "逻辑", "案例", "总结"] },
  "subtitles": { "languages": ["zh", "en"], "layout": "chinese_above_english", "safe_area_check": true },
  "storyboard": [
    { "scene_id": "S001", "start": 0, "end": 2, "visual_type": "cover",
      "motion": "subtle_push", "sfx": "soft_impact" },
    { "scene_id": "S002", "start": 2, "end": 5, "visual_type": "presenter",
      "cover_visible": false,
      "animation_plan": [
        { "time": 2, "action": "show_navigation" },
        { "time": 3, "action": "highlight_keyword" },
        { "time": 4, "action": "subtle_zoom" }
      ] }
  ]
}
```

正式执行时还必须带：素材绝对路径、精确帧号、真实字幕时间戳、图形坐标、动画曲线、授权信息、横竖屏安全区、头像取景参数。

---

## 十、跨 Agent 适配

同一套规则，任何 Agent 都能读；能否出片取决于环境。

| Agent | 读取方式 | 能否渲染 |
|---|---|---|
| Codex / Claude Code / Gemini CLI | `AGENTS.md` → `SKILL.md` | 是（需 ffmpeg + node） |
| 豆包工作 / WorkBuddy | 本 `SKILL.md` | 视环境 |
| 仅文本 LLM | 只输出 `director_plan.json` + `storyboard.json` | 否，交给渲染环境 |

**分工原则：推理归模型，渲染归程序。** 不要让大模型去猜像素，也不要让渲染引擎去做语义判断。

---

## 十一、交付清单

```
<选题名>/
├── 01_最终成片.mp4
├── 02_首帧封面.png
├── 03_精剪原声视频.mp4
├── 04_中英双语字幕.srt
├── 05_完整口播文稿.md
├── 06_全片导演计划.json
├── 07_逐秒分镜计划.json
├── 08_自动质检报告.md
└── 09_可编辑视频工程/
```

横竖屏双出时，各自生成一份成片、封面、分镜布局与字幕工程，共用内容分析与精剪时间轴。

---

## 十二、什么时候必须停下来报告

- 转写引擎不可用，且无替代方案 → 报告，不要瞎编台词。
- 原片严重模糊/无声/无有效讲解内容 → 报告，不要硬剪。
- 素材版权不明 → 不用，并说明原因。
- 渲染多次失败 → 报告错误原文，不要交出半成品冒充成片。

**诚实优于完成度。**
