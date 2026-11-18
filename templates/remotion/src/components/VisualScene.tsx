import React, { CSSProperties } from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Scene, ThemeConfig, fontOf, scaleFor } from "./theme";

type Props = { scene: Scene; theme: ThemeConfig; layout: any; vertical?: boolean };

const card = (theme: ThemeConfig): CSSProperties => ({
  background: theme.colors.surface,
  borderRadius: 18,
  padding: "26px 30px",
  border: `1px solid ${theme.colors.divider ?? "rgba(255,255,255,0.1)"}`,
  boxShadow: "0 12px 32px rgba(0,0,0,0.22)",
});

const heading = (theme: ThemeConfig, size: number): CSSProperties => ({
  fontFamily: fontOf(theme),
  fontSize: Math.round(size),
  fontWeight: 800,
  color: theme.colors.text_primary,
  lineHeight: 1.25,
});

/**
 * 通用知识画面渲染器：按 visual_type 分派到具体形态。
 * 覆盖 keyword / flow_steps / compare / chart / timeline / cards / citation /
 * causal_chain / summary / number_roll 等；未识别的类型退回“标题 + 正文”，保证不黑屏。
 */
export const VisualScene: React.FC<Props> = ({ scene, theme, layout, vertical }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = scaleFor(layout);
  const t = frame / fps;
  const c = scene.content ?? {};
  const vt = scene.visual_type;
  const appear = spring({ frame, fps, config: { damping: 200 }, durationInFrames: Math.round(0.5 * fps) });

  const padX = vertical ? 64 : 96;
  const padTop = vertical ? 336 : 132;
  const padBottom = vertical ? 300 : 120;
  const base: CSSProperties = {
    paddingTop: padTop,
    paddingBottom: padBottom,
    paddingLeft: padX,
    paddingRight: padX,
    fontFamily: fontOf(theme),
    color: theme.colors.text_primary,
    background: theme.colors.background,
  };
  const k = vertical ? 1 : s;

  const title = c.title ? (
    <div style={{ ...heading(theme, (vertical ? 58 : 64) * k), marginBottom: 40 }}>{c.title}</div>
  ) : null;

  if (vt === "keyword") {
    const words: string[] = c.keywords ?? c.words ?? [];
    const emphasis = Number(c.emphasis_index ?? 0);
    return (
      <AbsoluteFill style={{ ...base, justifyContent: "center", alignItems: "center" }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 28, justifyContent: "center" }}>
          {words.map((w, i) => {
            const local = spring({ frame: frame - Math.round(i * 0.25 * fps), fps, config: { damping: 200 } });
            return (
              <span
                key={i}
                style={{
                  fontSize: (vertical ? 76 : 88) * k,
                  fontWeight: 900,
                  color: i === emphasis ? theme.colors.accent : theme.colors.text_primary,
                  opacity: local,
                  transform: `translateY(${(1 - local) * 24}px)`,
                }}
              >
                {w}
              </span>
            );
          })}
        </div>
      </AbsoluteFill>
    );
  }

  if (vt === "flow_steps") {
    const nodes: string[] = c.nodes ?? [];
    const details: string[] = c.steps_detail ?? [];
    return (
      <AbsoluteFill style={base}>
        {title}
        <div
          style={{
            display: "flex",
            flexDirection: vertical ? "column" : "row",
            gap: vertical ? 18 : 26,
            alignItems: "stretch",
            flex: 1,
            justifyContent: "center",
          }}
        >
          {nodes.map((n, i) => {
            const local = spring({ frame: frame - Math.round(i * 0.3 * fps), fps, config: { damping: 200 } });
            return (
              <div key={n} style={{ ...card(theme), flex: 1, opacity: local, transform: `translateY(${(1 - local) * 20}px)` }}>
                <div style={{ fontSize: (vertical ? 22 : 24) * k, color: theme.colors.accent, fontWeight: 700 }}>
                  {String(i + 1).padStart(2, "0")}
                </div>
                <div style={{ ...heading(theme, (vertical ? 40 : 44) * k), marginTop: 8 }}>{n}</div>
                {details[i] ? (
                  <div style={{ marginTop: 10, fontSize: (vertical ? 22 : 24) * k, color: theme.colors.text_secondary, lineHeight: 1.5 }}>
                    {details[i]}
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    );
  }

  if (vt === "compare" || vt === "mindmap") {
    const left = c.left ?? { title: c.left_title ?? "A", items: c.left_items ?? [] };
    const right = c.right ?? { title: c.right_title ?? "B", items: c.right_items ?? [] };
    return (
      <AbsoluteFill style={base}>
        {title}
        <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", gap: 28, flex: 1 }}>
          {[left, right].map((col: any, ci: number) => {
            const local = spring({ frame: frame - Math.round((ci + 1) * 0.4 * fps), fps, config: { damping: 200 } });
            return (
              <div key={ci} style={{ ...card(theme), flex: 1, opacity: local, transform: `translateX(${(1 - local) * (ci ? 40 : -40)}px)` }}>
                <div style={{ fontSize: (vertical ? 30 : 32) * k, fontWeight: 800, color: ci ? theme.colors.accent : theme.colors.text_primary }}>
                  {col.title}
                </div>
                <div style={{ marginTop: 20, display: "flex", flexDirection: "column", gap: 14 }}>
                  {(col.items ?? []).map((it: string, i: number) => (
                    <div key={i} style={{ fontSize: (vertical ? 24 : 26) * k, color: theme.colors.text_secondary, lineHeight: 1.5 }}>
                      · {it}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    );
  }

  if (vt === "chart") {
    const series: Array<{ label: string; value: number }> = c.series ?? [];
    const max = Math.max(1, ...series.map((x) => Math.abs(x.value)));
    const grow = Math.min(1, t / 1.2);
    const maxBar = vertical ? 600 : 480;
    return (
      <AbsoluteFill style={base}>
        {title}
        <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", gap: vertical ? 16 : 40, flex: 1 }}>
          {series.map((d, i) => {
            const h = Math.max(10, Math.round((Math.abs(d.value) / max) * maxBar * grow));
            const negative = d.value < 0;
            return (
              <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "flex-end", alignItems: "center", gap: 12 }}>
                <div style={{ fontSize: (vertical ? 30 : 34) * k, fontWeight: 800, color: theme.colors.text_primary }}>
                  {Math.round(d.value * grow)}
                </div>
                <div
                  style={{
                    width: vertical ? "86%" : "62%",
                    height: h,
                    background: negative ? theme.colors.warning ?? "#C98B5E" : i === series.length - 1 ? theme.colors.accent : theme.colors.surface,
                    borderRadius: 10,
                  }}
                />
                <div style={{ fontSize: (vertical ? 22 : 25) * k, color: theme.colors.text_secondary }}>{d.label}</div>
              </div>
            );
          })}
        </div>
        {c.source ? (
          <div style={{ marginTop: 18, fontSize: (vertical ? 18 : 20) * k, color: theme.colors.text_secondary, opacity: 0.7 }}>
            {c.unit ? `单位：${c.unit} · ` : ""}来源：{c.source}
          </div>
        ) : null}
      </AbsoluteFill>
    );
  }

  if (vt === "timeline") {
    const events: Array<{ time: string; title: string; desc?: string }> = c.events ?? [];
    return (
      <AbsoluteFill style={base}>
        {title}
        <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", gap: vertical ? 22 : 26, flex: 1, alignItems: vertical ? "stretch" : "center" }}>
          {events.map((e, i) => {
            const local = spring({ frame: frame - Math.round(i * 0.4 * fps), fps, config: { damping: 200 } });
            return (
              <div key={i} style={{ ...card(theme), flex: 1, opacity: local, transform: `translateY(${(1 - local) * 18}px)` }}>
                <div style={{ fontSize: (vertical ? 20 : 22) * k, color: theme.colors.accent, fontWeight: 700 }}>{e.time}</div>
                <div style={{ ...heading(theme, (vertical ? 34 : 38) * k), marginTop: 10 }}>{e.title}</div>
                {e.desc ? (
                  <div style={{ marginTop: 10, fontSize: (vertical ? 21 : 23) * k, color: theme.colors.text_secondary, lineHeight: 1.5 }}>{e.desc}</div>
                ) : null}
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    );
  }

  if (vt === "cards") {
    const cards: Array<{ title: string; body: string }> = c.cards ?? [];
    return (
      <AbsoluteFill style={base}>
        {title}
        <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", flexWrap: "wrap", gap: 24, flex: 1 }}>
          {cards.map((cd, i) => {
            const local = spring({ frame: frame - Math.round(i * 0.35 * fps), fps, config: { damping: 160 } });
            return (
              <div key={i} style={{ ...card(theme), flex: vertical ? "none" : "1 1 28%", opacity: local, transform: `scale(${0.94 + local * 0.06})` }}>
                <div style={heading(theme, (vertical ? 34 : 36) * k)}>{cd.title}</div>
                <div style={{ marginTop: 12, fontSize: (vertical ? 22 : 24) * k, color: theme.colors.text_secondary, lineHeight: 1.55 }}>{cd.body}</div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    );
  }

  if (vt === "causal_chain") {
    const chain: Array<{ cause: string; effect: string }> = c.chain ?? [];
    return (
      <AbsoluteFill style={base}>
        {title}
        <div style={{ display: "flex", flexDirection: "column", gap: 18, flex: 1, justifyContent: "center" }}>
          {chain.map((row, i) => {
            const local = spring({ frame: frame - Math.round(i * 0.5 * fps), fps, config: { damping: 200 } });
            return (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 18, opacity: local }}>
                <div style={{ ...card(theme), flex: 1, borderLeft: `4px solid ${theme.colors.accent}` }}>
                  <div style={{ fontSize: (vertical ? 24 : 26) * k, color: theme.colors.text_primary }}>{row.cause}</div>
                </div>
                <div style={{ fontSize: 30, color: theme.colors.accent }}>→</div>
                <div style={{ ...card(theme), flex: 1 }}>
                  <div style={{ fontSize: (vertical ? 24 : 26) * k, color: theme.colors.text_secondary }}>{row.effect}</div>
                </div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    );
  }

  if (vt === "citation") {
    return (
      <AbsoluteFill style={base}>
        {title}
        <div style={{ ...card(theme), flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", padding: 48 }}>
          <div style={{ fontSize: (vertical ? 34 : 40) * k, lineHeight: 1.6, color: theme.colors.text_primary }}>{c.quote}</div>
          <div style={{ marginTop: 26, fontSize: (vertical ? 22 : 24) * k, color: theme.colors.accent }}>— {c.source}</div>
        </div>
      </AbsoluteFill>
    );
  }

  if (vt === "summary") {
    const points: string[] = c.points ?? [];
    return (
      <AbsoluteFill style={base}>
        {title}
        <div style={{ display: "flex", flexDirection: "column", gap: 18, flex: 1, justifyContent: "center" }}>
          {points.map((p, i) => {
            const local = spring({ frame: frame - Math.round(i * 0.4 * fps), fps, config: { damping: 200 } });
            return (
              <div key={i} style={{ display: "flex", gap: 18, alignItems: "center", opacity: local, transform: `translateX(${(1 - local) * 24}px)` }}>
                <div style={{ color: theme.colors.accent, fontSize: (vertical ? 28 : 32) * k, fontWeight: 800 }}>
                  {String(i + 1).padStart(2, "0")}
                </div>
                <div style={{ fontSize: (vertical ? 30 : 34) * k, color: theme.colors.text_primary, lineHeight: 1.4 }}>{p}</div>
              </div>
            );
          })}
        </div>
        {c.conclusion ? (
          <div style={{ marginTop: 28, fontSize: (vertical ? 34 : 38) * k, fontWeight: 900, color: theme.colors.accent }}>
            {c.conclusion}
          </div>
        ) : null}
      </AbsoluteFill>
    );
  }

  if (vt === "number_roll") {
    const value = Math.round((c.from ?? 0) + ((c.to ?? 100) - (c.from ?? 0)) * Math.min(1, t / 1.2));
    return (
      <AbsoluteFill style={{ ...base, justifyContent: "center", alignItems: "center" }}>
        <div style={{ fontSize: (vertical ? 150 : 180) * k, fontWeight: 900, color: theme.colors.accent }}>
          {value}
          <span style={{ fontSize: 48, marginLeft: 8, color: theme.colors.text_secondary }}>{c.unit ?? ""}</span>
        </div>
        {c.title ? (
          <div style={{ marginTop: 18, fontSize: (vertical ? 30 : 32) * k, color: theme.colors.text_secondary }}>{c.title}</div>
        ) : null}
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{ ...base, justifyContent: "center" }}>
      {title}
      <div style={{ fontSize: (vertical ? 26 : 28) * k, color: theme.colors.text_secondary, lineHeight: 1.7, opacity: appear }}>
        {c.text ?? c.quote ?? ""}
      </div>
    </AbsoluteFill>
  );
};
