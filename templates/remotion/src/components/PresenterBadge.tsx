import React from "react";
import { OffthreadVideo, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { ThemeConfig } from "./theme";

type Props = {
  /** 口播原片地址（本地 HTTP 服务或公网 URL） */
  src: string;
  /** 该镜头在源视频中的起始帧（绝对帧，不受 Sequence 影响） */
  startFrom: number;
  theme: ThemeConfig;
  vertical?: boolean;
  /** 圆直径，缺省竖屏 192 / 横屏 240 */
  size?: number;
  /** 人脸中心在源画面高度的比例位置（竖屏口播常见 0.28–0.34） */
  focus?: number;
  /** 人脸中心在源画面宽度的比例位置 */
  focusX?: number;
  /**
   * 取景倍数 = 内层画面宽度 / 圆直径。
   * 0.85–1.0：露出头发 + 全脸 + 双肩（推荐）；
   * 1.1–1.4：人物在画面里偏小时放大；
   * >1.5：只剩头肩特写（会牺牲肩膀，慎用）
   */
  zoom?: number;
  /** 源视频宽高比（width/height），用于按比例推算内层高度 */
  srcAspect?: number;
  /** 头像与画面右边缘的距离 */
  margin?: number;
  /** 距画面顶部的距离 */
  top?: number;
  /** 人脸中心在圆内的纵向位置（0.42 圆心略下，上方留给头发） */
  anchorY?: number;
};

/**
 * 真人圆形头像（右上角常驻）。
 * 取景要求：圆内必须露出头发 + 完整五官 + 双肩，不允许裁额头或下巴。
 * 位置要求：压在导航条下方、内容区之上，任何情况下不遮挡标题与知识卡片。
 */
export const PresenterBadge: React.FC<Props> = ({
  src,
  startFrom,
  theme,
  vertical,
  size,
  focus = 0.30,
  focusX = 0.58,
  zoom = 0.95,
  srcAspect = 0.5625,
  margin,
  top,
  anchorY = 0.42,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!src) return null;

  const D = size ?? (vertical ? 192 : 240);
  const m = margin ?? (vertical ? 48 : 52);
  // 竖屏放在导航条（y 230–300）之下，横屏放在顶部右侧
  const t0 = top ?? (vertical ? 316 : 152);

  // 内层画面尺寸：宽度由取景倍数决定，高度按源片真实宽高比推算
  const innerW = D * zoom;
  const innerH = innerW / Math.max(0.3, srcAspect);
  // 人脸中心锚定到圆内 anchorY 处：上方留头发空间，下方留肩膀与衣领
  const left = D / 2 - focusX * innerW;
  const offsetTop = D * anchorY - focus * innerH;

  // 入场：0.4s 内轻微放大淡入，避免硬切
  const enter = spring({
    frame,
    fps,
    config: { damping: 200 },
    durationInFrames: Math.round(0.4 * fps),
  });

  const lightBg =
    (() => {
      const h = theme.colors.background.replace("#", "");
      if (h.length < 6) return false;
      const r = parseInt(h.slice(0, 2), 16), g = parseInt(h.slice(2, 4), 16), b = parseInt(h.slice(4, 6), 16);
      return (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.6;
    })();

  return (
    <div
      style={{
        position: "absolute",
        right: m,
        top: t0,
        width: D,
        height: D,
        borderRadius: "50%",
        overflow: "hidden",
        border: `3px solid ${lightBg ? "rgba(255,255,255,0.94)" : "rgba(255,255,255,0.26)"}`,
        boxShadow: lightBg
          ? "0 12px 30px rgba(23,60,57,0.20), 0 0 0 6px rgba(255,255,255,0.10)"
          : "0 14px 34px rgba(0,0,0,0.48), 0 0 0 6px rgba(255,255,255,0.05)",
        opacity: enter,
        transform: `scale(${interpolate(enter, [0, 1], [0.92, 1])})`,
        backgroundColor: theme.colors.surface,
      }}
    >
      <OffthreadVideo
        src={src}
        startFrom={startFrom}
        style={{
          position: "absolute",
          width: innerW,
          height: innerH,
          objectFit: "cover",
          left,
          top: offsetTop,
        }}
      />
    </div>
  );
};
