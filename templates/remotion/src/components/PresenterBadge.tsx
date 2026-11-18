import React from "react";
import { OffthreadVideo, interpolate } from "remotion";
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
  /** 圆心在源画面高度的比例位置，0.34 ≈ 人脸中心 */
  focus?: number;
  /** 圆心在源画面宽度的比例位置，0.62 ≈ 人物所在位置 */
  focusX?: number;
  /** 取景放大倍数：近景口播 1.0；人物偏小（全身机位）1.2–1.8 */
  zoom?: number;
  /** 头像与画面边缘的距离 */
  margin?: number;
  /** 距画面顶部的距离 */
  top?: number;
  /** 入场：0→1，避免硬切 */
  fade?: number;
};

/**
 * 真人圆形头像（右上角常驻）。
 * 取景要求：圆形内必须露出完整五官 + 头发 + 上半身肩膀，不得裁到额头或下巴。
 * 位置要求：压在导航条下方、文字区之上，任何情况下不遮挡标题与知识内容。
 */
export const PresenterBadge: React.FC<Props> = ({
  src,
  startFrom,
  theme,
  vertical,
  size,
  focus = 0.34,
  focusX = 0.62,
  zoom = 1.0,
  margin,
  top,
  fade = 1,
}) => {
  if (!src) return null;
  const D = size ?? (vertical ? 192 : 240);
  const m = margin ?? (vertical ? 48 : 52);
  // 竖屏放在导航条（约 y 230–300）之下，横屏放在顶部右侧
  const t0 = top ?? (vertical ? 312 : 152);
  // 内层画面：宽度略大于圆径，高度按 9:16 竖片比例推算，保证同时容纳头发、全脸与肩部
  const innerW = D * 1.02 * zoom;
  const innerH = innerW * (1280 / 720);
  // 水平方向按人物实际位置取景，避免人物偏在圆外
  const left = D / 2 - focusX * innerW;
  // 让源画面 focus（人脸中心）处正好落在圆心
  const offsetTop = D / 2 - focus * innerH;

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
        border: `3px solid ${lightBg ? "rgba(255,255,255,0.92)" : "rgba(255,255,255,0.22)"}`,
        boxShadow: lightBg ? "0 10px 26px rgba(23,60,57,0.18)" : "0 12px 30px rgba(0,0,0,0.45)",
        opacity: fade,
        transform: `scale(${interpolate(fade, [0, 1], [0.9, 1])})`,
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
