import React from "react";
import { SubItem, ThemeConfig, fontOf, scaleFor } from "./theme";

type Props = { item: SubItem; theme: ThemeConfig; layout: any; vertical?: boolean };

/** 逐句双语字幕：中文在上（48–60px），英文在下（30–38px），只在安全区内。
 * 注意：不要使用 AbsoluteFill，它自带 width:100%，与 left/right 同用会使字幕右移。
 */
export const SubtitleLine: React.FC<Props> = ({ item, theme, layout, vertical }) => {
  const s = scaleFor(layout);
  const key = vertical ? "vertical" : "horizontal";
  const zhPx = Math.round(theme.typography.subtitle_zh_px[key] * (vertical ? 1 : s));
  const enPx = Math.round(theme.typography.subtitle_en_px[key] * (vertical ? 1 : s));
  const top = vertical ? 1450 : 936;

  return (
    <div
      style={{
        position: "absolute",
        top,
        bottom: vertical ? 200 : 36,
        left: vertical ? 56 : 96,
        right: vertical ? 56 : 96,
        flexDirection: "column",
        justifyContent: "flex-start",
        alignItems: "center",
        fontFamily: fontOf(theme),
        display: "flex",
      }}
    >
      <div
        style={{
          maxWidth: "100%",
          textAlign: "center",
          padding: vertical ? "6px 14px" : "4px 16px",
          borderRadius: 10,
          background: vertical ? "rgba(0,0,0,0.42)" : "rgba(0,0,0,0.28)",
        }}
      >
        <div style={{ fontSize: zhPx, fontWeight: 700, color: theme.colors.text_primary, lineHeight: 1.28 }}>
          {item.zh}
        </div>
        {item.en ? (
          <div style={{ fontSize: enPx, color: theme.colors.text_secondary, lineHeight: 1.3, marginTop: vertical ? 8 : 6 }}>
            {item.en}
          </div>
        ) : null}
      </div>
    </div>
  );
};
