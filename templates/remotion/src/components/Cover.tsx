import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { ThemeConfig, fontOf } from "./theme";

type Props = {
  theme: ThemeConfig;
  lines: string[];
  emphasisIndex?: number;
  vertical?: boolean;
};

/**
 * 首帧即封面。
 * 第 0 帧标题必须已经完整、静态、可读；动画只是“呼吸”（轻推 + 关键词渐亮）。
 */
export const Cover: React.FC<Props> = ({ theme, lines, emphasisIndex = 1, vertical }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const push = interpolate(t, [0, 1.4], [1.0, 1.04], { extrapolateRight: "clamp" });
  const glow = interpolate(t, [0.6, 1.2], [0.72, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const titleSize = vertical ? theme.typography.title_px.vertical : theme.typography.title_px.horizontal;
  const subSize = Math.round(titleSize * 0.62);

  return (
    <AbsoluteFill style={{ background: theme.colors.background }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 42%, ${theme.colors.surface} 0%, ${theme.colors.background} 68%)`,
          opacity: 0.9,
        }}
      />
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          transform: `scale(${push})`,
          fontFamily: fontOf(theme),
          padding: vertical ? "0 72px" : "0 160px",
        }}
      >
        {lines.map((line, i) => (
          <div
            key={i}
            style={{
              fontSize: i === 0 ? titleSize : subSize,
              fontWeight: 900,
              lineHeight: 1.14,
              letterSpacing: 2,
              color: i === emphasisIndex ? theme.colors.accent : theme.colors.text_primary,
              opacity: i === emphasisIndex ? glow : 1,
              textAlign: "center",
              marginTop: i === 0 ? 0 : 12,
            }}
          >
            {line}
          </div>
        ))}
        <div
          style={{
            marginTop: 46,
            width: 120,
            height: 4,
            background: theme.colors.accent,
            opacity: 0.85,
            borderRadius: 4,
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
