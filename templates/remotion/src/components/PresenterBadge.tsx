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
  /** 人脸中心在源画面高度的比例位置 */
  focus?: number;
  /** 人脸中心在源画面宽度的比例位置 */
  focusX?: number;
  /** 头部高度（发顶→下巴）占源画面高度的比例，量一次即可，缺省 0.30 */
  headRatio?: number;
  /** 取景倍数（内层宽度 / 圆直径）。缺省按 headRatio 自动算，且不会 < 1（绝不越出原片） */
  zoom?: number;
  /** 源视频宽高比（width/height） */
  srcAspect?: number;
  /** 头像与画面右边缘的距离 */
  margin?: number;
  /** 距画面顶部的距离 */
  top?: number;
};

/**
 * 真人圆形头像（右上角常驻，V1.0.3 自动取景）。
 * 规则：
 *  1) 圆内必须同时露出头发、完整五官（含下巴）、双肩；
 *  2) 取景窗口绝不越出原片画面（start 夹在 [0, 1-window] 内，zoom 不小于 1）；
 *  3) 头发顶部固定留 6% 窗口高度，剩余全部给肩颈。
 */
export const PresenterBadge: React.FC<Props> = ({
  src,
  startFrom,
  theme,
  vertical,
  size,
  focus = 0.33,
  focusX = 0.55,
  headRatio = 0.30,
  zoom,
  srcAspect = 0.5625,
  margin,
  top,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!src) return null;

  const D = size ?? (vertical ? 192 : 240);
  const m = margin ?? (vertical ? 48 : 52);
  const t0 = top ?? (vertical ? 316 : 152);

  const aspect = Math.max(0.3, srcAspect);

  // 目标：头部占圆直径 55%；窗口高度 = 源片高度的 windowFrac。
  // windowFrac 最大到整幅宽（aspect），所以 zoom 不会 < 1 —— 保证不越出原片内容。
  const targetHeadFill = 0.55;
  const neededWindow = headRatio / targetHeadFill;
  const z = Math.max(1, zoom ?? aspect / Math.min(neededWindow, aspect));
  const windowFrac = Math.min(1, aspect / z);

  const innerW = D * z;
  const innerH = innerW / aspect;

  // 头发顶部留 6% 窗口，其余给肩颈；再夹到原片边界内
  const headTop = focus - headRatio / 2;
  const topPad = 0.06 * windowFrac;
  const maxStart = Math.max(0, 1 - windowFrac);
  const start = Math.min(Math.max(0, headTop - topPad), maxStart);

  const left = D / 2 - focusX * innerW;
  const offsetTop = -start * innerH;

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
