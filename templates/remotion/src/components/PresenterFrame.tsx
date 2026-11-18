import React from "react";
import { AbsoluteFill, OffthreadVideo, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { Scene, ThemeConfig, fontOf, scaleFor } from "./theme";

type Props = {
  scene: Scene;
  theme: ThemeConfig;
  layout: any;
  presenterVideo?: string;
  vertical?: boolean;
};

/**
 * 真人镜头。有 video 时铺满/侧条；无视频时渲染品牌化占位面板，
 * 保证预览与分镜节奏可评估（正式出片必须提供 presenterVideo）。
 */
export const PresenterFrame: React.FC<Props> = ({ scene, theme, layout, presenterVideo, vertical }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = scaleFor(layout);
  const t = frame / fps;
  const zoom = interpolate(t, [0, 3], [1.0, 1.03], { extrapolateRight: "clamp" });
  const pip = scene.visual_type === "presenter_pip";
  const mediaStart = Number(scene.content?.mediaStart ?? scene.start);
  const from = Math.round(mediaStart * fps);

  const media = presenterVideo ? (
    <OffthreadVideo
      src={presenterVideo}
      startFrom={from}
      style={{
        width: "100%",
        height: "100%",
        objectFit: "cover",
        transform: `scale(${zoom})`,
      }}
    />
  ) : (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        background: `linear-gradient(140deg, ${theme.colors.surface} 0%, ${theme.colors.background} 100%)`,
        transform: `scale(${zoom})`,
        fontFamily: fontOf(theme),
      }}
    >
      <div
        style={{
          width: 240,
          height: 240,
          borderRadius: "50%",
          background: theme.colors.accent,
          opacity: 0.16,
          marginBottom: 28,
        }}
      />
      <div style={{ color: theme.colors.text_secondary, fontSize: Math.round(28 * (vertical ? 1 : s)) }}>
        {scene.content?.focus || "真人出镜画面"}
      </div>
    </AbsoluteFill>
  );

  if (!pip) {
    return <AbsoluteFill style={{ background: theme.colors.background }}>{media}</AbsoluteFill>;
  }

  return (
    <AbsoluteFill style={{ background: theme.colors.background }}>
      <div style={{ position: "absolute", left: 0, right: vertical ? 0 : "38%", top: 0, bottom: 0 }}>{media}</div>
      <div
        style={{
          position: "absolute",
          left: vertical ? 0 : "40%",
          right: vertical ? 0 : 96,
          top: vertical ? "62%" : 96,
          bottom: 96,
          padding: 40,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          fontFamily: fontOf(theme),
          color: theme.colors.text_primary,
        }}
      >
        <div style={{ fontSize: Math.round(46 * (vertical ? 1 : s)), fontWeight: 800, lineHeight: 1.3 }}>
          {scene.content?.focus || scene.content?.title || ""}
        </div>
        {Array.isArray(scene.content?.points) ? (
          <div style={{ marginTop: 24, display: "flex", flexDirection: "column", gap: 14 }}>
            {(scene.content.points as string[]).map((p, i) => (
              <div key={i} style={{ fontSize: Math.round(30 * (vertical ? 1 : s)), color: theme.colors.text_secondary }}>
                {p}
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
