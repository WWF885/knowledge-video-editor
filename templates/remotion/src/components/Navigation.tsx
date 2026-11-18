import React, { useRef } from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { ThemeConfig, fontOf, scaleFor } from "./theme";

type Props = {
  theme: ThemeConfig;
  chapters: string[];
  activeIndex: number;
  layout: any;
  vertical?: boolean;
};

/**
 * 顶部动态章节导航（V1.0.2 重设计）。
 * 视觉：胶囊底 + 毛玻璃 + 细描边 + 柔和投影；当前章用一块随切换滑动的强调块高亮，
 * 已完成章保留一个强调色圆点，未开始章低调处理；底部一条极细的整片进度线。
 * 尺寸：竖屏高 76、距顶 230（封面期间由父组件隐藏）；横屏高 84、距顶 20，占高 ≤8%。
 */
export const Navigation: React.FC<Props> = ({ theme, chapters, activeIndex, layout, vertical }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = scaleFor(layout);
  const resW = layout?.resolution?.[0] ?? 1080;

  const _bg = theme.colors.background.replace("#", "");
  const lightTheme =
    (0.299 * parseInt(_bg.slice(0, 2), 16) + 0.587 * parseInt(_bg.slice(2, 4), 16) + 0.114 * parseInt(_bg.slice(4, 6), 16)) / 255 > 0.6;

  const marginX = vertical ? 40 : 96;
  const height = Math.round((vertical ? 76 : 84) * (vertical ? 1 : s));
  const pad = Math.round(8 * (vertical ? 1 : s));
  const barW = resW - marginX * 2;
  const chipW = barW / Math.max(1, chapters.length);
  const fontPx = Math.round((vertical ? 27 : 28) * (vertical ? 1 : s));

  // 切章时强调块平滑滑动（0.4s）
  const fromRef = useRef(activeIndex);
  const toRef = useRef(activeIndex);
  const changedAt = useRef(-999);
  if (activeIndex !== toRef.current) {
    fromRef.current = toRef.current;
    toRef.current = activeIndex;
    changedAt.current = frame;
  }
  const slide = spring({
    frame: frame - changedAt.current,
    fps,
    config: { damping: 200 },
    durationInFrames: Math.round(0.4 * fps),
  });
  const pillX = interpolate(slide, [0, 1], [fromRef.current * chipW, toRef.current * chipW]);
  const doneRatio = Math.min(1, (toRef.current + 1) / Math.max(1, chapters.length));

  return (
    <div
      style={{
        position: "absolute",
        top: vertical ? 230 : 20,
        left: marginX,
        right: marginX,
        height,
        borderRadius: height / 2,
        padding: pad,
        boxSizing: "border-box",
        display: "flex",
        alignItems: "stretch",
        fontFamily: fontOf(theme),
        background: lightTheme ? "rgba(255,255,255,0.90)" : "rgba(18,22,34,0.46)",
        border: `1px solid ${lightTheme ? "rgba(23,60,57,0.12)" : "rgba(255,255,255,0.12)"}`,
        boxShadow: lightTheme
          ? "0 10px 24px rgba(23,60,57,0.10)"
          : "0 12px 28px rgba(0,0,0,0.34)",
        backdropFilter: "blur(10px)",
        overflow: "hidden",
      }}
    >
      {/* 当前章滑动强调块 */}
      <div
        style={{
          position: "absolute",
          top: pad,
          left: pad + pillX,
          width: chipW,
          height: height - pad * 2,
          borderRadius: (height - pad * 2) / 2,
          background: lightTheme ? "rgba(23,60,57,0.10)" : "rgba(255,255,255,0.14)",
          boxShadow: lightTheme
            ? "inset 0 0 0 1px rgba(23,60,57,0.10)"
            : "inset 0 0 0 1px rgba(255,255,255,0.10)",
        }}
      />

      {chapters.map((c, i) => {
        const active = i === toRef.current;
        const done = i < toRef.current;
        return (
          <div
            key={c}
            style={{
              position: "relative",
              width: chipW,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: Math.round(fontPx * 0.34),
            }}
          >
            <span
              style={{
                width: active ? 8 : 6,
                height: active ? 8 : 6,
                borderRadius: 4,
                background: done || active ? theme.colors.accent : "transparent",
                border: done || active
                  ? `1px solid ${theme.colors.accent}`
                  : `1px solid ${lightTheme ? "rgba(23,60,57,0.22)" : "rgba(255,255,255,0.22)"}`,
                opacity: active ? 1 : done ? 0.9 : 0.6,
                flex: "0 0 auto",
              }}
            />
            <span
              style={{
                fontSize: fontPx,
                fontWeight: active ? 800 : 600,
                letterSpacing: 0.5,
                color: active ? theme.colors.text_primary : theme.colors.text_secondary,
                opacity: active ? 1 : done ? 0.88 : 0.52,
                whiteSpace: "nowrap",
              }}
            >
              {c}
            </span>
          </div>
        );
      })}

      {/* 整片进度：底部极细线 */}
      <div
        style={{
          position: "absolute",
          left: 0,
          bottom: 0,
          height: 2,
          width: `${Math.round(doneRatio * 100)}%`,
          background: theme.colors.accent,
          opacity: 0.55,
          borderRadius: 2,
        }}
      />
    </div>
  );
};
