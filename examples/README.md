# 示例 · 四类导演计划

每个目录一份 `storyboard.json`，都是**可通过 `validate_storyboard.py` 校验**的完整契约样本。

| 目录 | 类型 | 比例 | 时长 | 看点 |
|---|---|---|---|---|
| `knowledge/` | 知识科普 | 16:9 | 96s | 对比图 → 流程 → 因果链 → 数据 → 时间轴 → 卡片 → 引用 → 总结，13 个镜头全覆盖 |
| `practice/` | 工具实操 | 9:16 | 58s | 录屏引导 + 竖屏上下分区 + 步骤导航 |
| `analysis/` | 商业分析 | 16:9 | 44s | 数据下滑 + 三层归因 + 结构失衡 + 判断 |
| `story/` | 故事分享 | 9:16 | 40s | 珍珠墨绿主题 + 时间轴叙事 + 认知反差 |

## 用法

```bash
# 校验
python3 scripts/validate_storyboard.py --storyboard examples/knowledge/storyboard.json

# 直接渲染（需要原声与字幕）
python3 scripts/render_video.py --storyboard examples/knowledge/storyboard.json \
    --audio work/edited.mp4 --out output/01_最终成片.mp4 --cover output/02_首帧封面.png
```

## 注意

- 示例里的 `content` 是示意内容，不是真实数据。`source` 字段刻意标注“示例数据”，提醒你换成可核实来源。
- `subtitles.source` 指向 `work/subtitle.json`，缺失时渲染会退化为无字幕（质检会扣分）。
- 这些示例是**结构范本**，不是“填空模板”。真实创作仍要按 `references/01` 判断类型、按 `06/07` 设计画面。
