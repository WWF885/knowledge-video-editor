import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { ThemeConfig, fontOf, scaleFor } from "./theme";

type Props = {
  theme: ThemeConfig;
  chapters: string[];
  activeIndex: number;
  layout: any;
  vertical?: boolean;
};

/**
 * 横屏顶部动态章节导航。
 * 高度 ≤ 画面 8%；封面期间由父组件隐藏；当前章高亮，已完成弱化，未开始低调。
 * 注意：不要使用 AbsoluteFill（自带 width:100%），否则 left/right 同时生效会整体偏移。
 */
export const Navigation: React.FC<Props> = ({ theme, chapters, activeIndex, layout, vertical }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = scaleFor(layout);
  const height = Math.round((vertical ? 76 : 84) * (vertical ? 1 : s) * 0.92);
  const fontPx = Math.round((vertical ? 30 : 32) * (vertical ? 1 : s));

  const total = chapters.length;
  const progress = total > 1 ? (activeIndex + 0.5) / total : 1;

  return (
    <div
      style={{
        position: "absolute",
        height,
        top: vertical ? 230 : 18,
        left: vertical ? 40 : 96,
        right: vertical ? 40 : 96,
        flexDirection: "row",
        alignItems: "center",
        gap: vertical ? 10 : 28,
        padding: "0 12px",
        fontFamily: fontOf(theme),
        backgroundColor: vertical ? "rgba(0,0,0,0.34)" : "rgba(0,0,0,0.20)",
        borderRadius: 14,
        display: "flex",
      }}
    >
      {chapters.map((c, i) => {
        const active = i === activeIndex;
        const done = i < activeIndex;
        const opacity = active ? 1 : done ? 0.45 : 0.25;
        return (
          <div key={c} style={{ display: "flex", alignItems: "center", gap: 8, opacity }}>
            {done ? <span style={{ color: theme.colors.accent, fontSize: fontPx * 0.9 }}>✓</span> : null}
            <span
              style={{
                fontSize: active ? fontPx * 1.08 : fontPx,
                fontWeight: active ? 800 : 600,
                color: active ? theme.colors.text_primary : theme.colors.text_secondary,
              }}
            >
              {c}
            </span>
            {active ? (
              <div
                style={{
                  height: 3,
                  width: Math.max(24, fontPx * 1.6),
                  background: theme.colors.accent,
                  borderRadius: 2,
                  opacity: 0.9,
                }}
              />
            ) : null}
          </div>
        );
      })}
      <div style={{ flex: 1 }} />
      <div
        style={{
          width: vertical ? 90 : 180,
          height: 3,
          background: theme.colors.surface,
          borderRadius: 2,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${Math.round(progress * 100)}%`,
            height: "100%",
            background: theme.colors.accent,
            opacity: 0.85,
          }}
        />
      </div>
    </div>
  );
};
