import React from "react";
import { AbsoluteFill, OffthreadVideo, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { ThemeConfig, fontOf } from "./theme";

type Props = {
  theme: ThemeConfig;
  lines: string[];
  emphasisIndex?: number;
  vertical?: boolean;
  /** 原片地址：封面以原片画面为底 */
  videoSrc?: string;
  /** 原片起始帧 */
  startFrom?: number;
};

/**
 * 首帧即封面（V1.0.3）。
 * 底：原视频画面（轻推 + 压暗/提亮蒙层）；
 * 面：两行超大艺术字，每行 ≤ 4 字，逐行拟合到"刚好铺满不越界"；
 * 封面期间不出现任何其他文字（字幕由 Video 层在封面段过滤）。
 */
export const Cover: React.FC<Props> = ({
  theme,
  lines,
  emphasisIndex = 1,
  vertical,
  videoSrc,
  startFrom = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;

  const push = interpolate(t, [0, 1.6], [1.02, 1.0], { extrapolateRight: "clamp" });
  const glow = interpolate(t, [0.5, 1.2], [0.86, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // 字号：逐行拟合——汉字按 1em、拉丁字符按 0.56em 估宽，左右各留 7%，
  // 每行都做到"刚好铺满不越界"，且总高度不超画面 34%。
  const effLen = (s: string) =>
    [...s].reduce((a, ch) => a + (/[\x00-\x7F]/.test(ch) ? 0.56 : 1), 0);
  const byHeight = height * (vertical ? 0.30 : 0.34);
  const lineSizes = lines.slice(0, 2).map((l) =>
    Math.round(Math.min(byHeight, (width * 0.86) / Math.max(1, effLen(l)))),
  );
  const fontSize = lineSizes[0] ?? byHeight;

  const _bg = theme.colors.background.replace("#", "");
  const lightTheme =
    (0.299 * parseInt(_bg.slice(0, 2), 16) + 0.587 * parseInt(_bg.slice(2, 4), 16) + 0.114 * parseInt(_bg.slice(4, 6), 16)) / 255 > 0.6;

  return (
    <AbsoluteFill style={{ backgroundColor: theme.colors.background, overflow: "hidden" }}>
      {/* 底：原视频画面 */}
      {videoSrc ? (
        <AbsoluteFill style={{ transform: `scale(${push})` }}>
          <OffthreadVideo
            src={videoSrc}
            startFrom={startFrom}
            muted
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </AbsoluteFill>
      ) : null}

      {/* 蒙层：保证大字可读，同时看得见人 */}
      <AbsoluteFill
        style={{
          background: lightTheme
            ? "linear-gradient(180deg, rgba(255,255,255,0.46) 0%, rgba(255,255,255,0.30) 40%, rgba(255,255,255,0.70) 100%)"
            : "linear-gradient(180deg, rgba(8,12,22,0.50) 0%, rgba(8,12,22,0.34) 40%, rgba(8,12,22,0.72) 100%)",
        }}
      />

      {/* 大字标题：整体居中偏上，最多两行 */}
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          transform: `scale(${push}) translateY(${Math.round(-height * 0.04)}px)`,
          fontFamily: fontOf(theme),
          padding: `0 ${Math.round(width * 0.05)}px`,
        }}
      >
        {lines.slice(0, 2).map((line, i) => {
          const emphasized = i === emphasisIndex;
          const fs = lineSizes[i] ?? fontSize;
          return (
            <div
              key={i}
              style={{
                fontSize: fs,
                fontWeight: 900,
                lineHeight: 1.06,
                letterSpacing: Math.round(fs * 0.01),
                color: emphasized ? theme.colors.accent : theme.colors.text_primary,
                opacity: emphasized ? glow : 1,
                textAlign: "center",
                marginTop: i === 0 ? 0 : Math.round(fontSize * 0.12),
                textShadow: lightTheme
                  ? "0 6px 22px rgba(255,255,255,0.55)"
                  : "0 8px 28px rgba(0,0,0,0.55)",
                whiteSpace: "nowrap",
              }}
            >
              {line}
            </div>
          );
        })}
        <div
          style={{
            marginTop: Math.round(fontSize * 0.18),
            width: Math.round(fontSize * 0.62),
            height: Math.max(3, Math.round(fontSize * 0.018)),
            background: theme.colors.accent,
            opacity: 0.9,
            borderRadius: 4,
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
