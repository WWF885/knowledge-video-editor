# assets · 素材说明

仓库里**不打包**字体、图标、音乐、音效的二进制文件（体积大、授权各异）。这里只说明放什么、怎么放、怎么登记。

## fonts/

必需的中文字体（任选其一，放进去即可）：

| 字体 | 用途 | 授权 |
|---|---|---|
| 思源黑体 Source Han Sans SC（Heavy / Bold） | 封面、标题、字幕 | SIL OFL 1.1，可商用 |
| 阿里巴巴普惠体 Bold | 标题替代 | 免费商用 |
| 思源宋体 Source Han Serif SC | 珍珠墨绿主题标题 | SIL OFL 1.1 |

放好之后，`config/*.json` 里的 `font_family` 与之一致，Remotion 才能正确回退。

## icons/

线性图标建议统一风格（stroke 2px、24×24 视框），放 SVG 原名即可。示例命名：`flow.svg`、`chart.svg`、`quote.svg`。

## music/

BGM 放在这里，并在 `CREDITS.md` 登记。**禁止**：来源不明、平台爆款、有明显旋律记忆点的流行曲。

## sound-effects/

本 Skill 需要的音效清单：

| 文件 | 对应 sfx name | 说明 |
|---|---|---|
| `soft_impact.wav` | `soft_impact` | 封面轻击 |
| `click.wav` | `click` | 关键词出现 |
| `pop.wav` | `pop` | 卡片落位 |
| `whoosh.wav` | `whoosh` | 节点连线、过渡 |
| `tick.wav` | `tick` | 数字滚动 |
| `soft_emphasis.wav` | `soft_emphasis` | 结论强调 |

全部要求：44.1/48kHz、单声道、时长 0.1–1.0s、无版权争议。

## CREDITS.md 模板

```markdown
| 文件 | 类型 | 来源 | 授权 | 获取日期 |
|---|---|---|---|---|
| bgm_minimal_01.mp3 | BGM | 自购 · Artlist | 商用授权 | 2026-11-01 |
| whoosh.wav | 音效 | CC0 · freesound #xxxxx | CC0 | 2026-11-01 |
```
