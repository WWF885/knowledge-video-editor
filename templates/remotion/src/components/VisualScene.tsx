import React, { CSSProperties } from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring } from "remotion";
import { Scene, ThemeConfig, fontOf, scaleFor } from "./theme";

type Props = { scene: Scene; theme: ThemeConfig; layout: any; vertical?: boolean };

const T = (n: number): number => Math.round(n * 1.12);

const isLight = (hex: string): boolean => {
  const h = (hex ?? "").replace("#", "");
  if (h.length < 6) return false;
  const r = parseInt(h.slice(0, 2), 16), g = parseInt(h.slice(2, 4), 16), b = parseInt(h.slice(4, 6), 16);
  return (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.6;
};

const card = (theme: ThemeConfig): CSSProperties => ({
  background: theme.colors.surface,
  borderRadius: 18,
  padding: "26px 30px",
  border: `1px solid ${isLight(theme.colors.background) ? "rgba(23,60,57,0.20)" : (theme.colors.divider ?? "rgba(255,255,255,0.1)")}`,
  boxShadow: isLight(theme.colors.background) ? "0 10px 26px rgba(23,60,57,0.12)" : "0 12px 32px rgba(0,0,0,0.22)",
});

const heading = (theme: ThemeConfig, size: number): CSSProperties => ({
  fontFamily: fontOf(theme),
  fontSize: T(size),
  fontWeight: 800,
  color: theme.colors.text_primary,
  lineHeight: 1.25,
});

/**
 * 通用知识画面渲染器：按 visual_type 分派到具体形态。
 * 覆盖 keyword / flow_steps / compare / chart / timeline / cards / citation /
 * causal_chain / summary / mindmap / org_tree / map / icon_story / number_roll 等。
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
  // 横屏时右侧为圆形头像预留安全区
  const padRight = vertical ? padX : padX + 344;
  const padTop = vertical ? 528 : 176;
  const padBottom = vertical ? 500 : 130;
  const base: CSSProperties = {
    paddingTop: padTop,
    paddingBottom: padBottom,
    paddingLeft: padX,
    paddingRight: padRight,
    fontFamily: fontOf(theme),
    color: theme.colors.text_primary,
    background: theme.colors.background,
  };

  const title = c.title ? (
    <div style={{ ...heading(theme, (vertical ? 58 : 64) * (vertical ? 1 : s)), marginBottom: 40 }}>
      {c.title}
    </div>
  ) : null;

  if (vt === "keyword") {
    const words: string[] = c.keywords ?? c.words ?? [];
    const emphasis = Number(c.emphasis_index ?? 0);
    return (
      <AbsoluteFill style={{ ...base, justifyContent: "center", alignItems: "center" }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 28, justifyContent: "center" }}>
          {words.map((w, i) => {
            const local = spring({ frame: frame - Math.round(i * 0.12 * fps), fps, config: { damping: 200 }, durationInFrames: Math.round(0.36 * fps) });
            return (
              <span
                key={i}
                style={{
                  fontSize: T(vertical ? 76 : 88) * (vertical ? 1 : s),
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
        <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", gap: vertical ? 18 : 26, alignItems: "stretch", flex: 1, justifyContent: "center" }}>
          {nodes.map((n, i) => {
            const local = spring({ frame: frame - Math.round(i * 0.15 * fps), fps, config: { damping: 200 }, durationInFrames: Math.round(0.36 * fps) });
            return (
              <div key={n} style={{ ...card(theme), flex: vertical ? "0 0 auto" : 1, opacity: local, transform: `translateY(${(1 - local) * 20}px)` }}>
                <div style={{ fontSize: T(vertical ? 22 : 24) * (vertical ? 1 : s), color: theme.colors.accent, fontWeight: 700 }}>
                  {String(i + 1).padStart(2, "0")}
                </div>
                <div style={{ ...heading(theme, (vertical ? 42 : 44) * (vertical ? 1 : s)), marginTop: 8 }}>{n}</div>
                {details[i] ? (
                  <div style={{ marginTop: 10, fontSize: T(vertical ? 24 : 24) * (vertical ? 1 : s), color: theme.colors.text_secondary, lineHeight: 1.5 }}>
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
        <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", gap: 24, flex: 1, justifyContent: "center" }}>
          {[left, right].map((col: any, ci: number) => {
            const local = spring({ frame: frame - Math.round(ci * 0.18 * fps), fps, config: { damping: 200 }, durationInFrames: Math.round(0.36 * fps) });
            return (
              <div key={ci} style={{ ...card(theme), flex: vertical ? "0 0 auto" : 1, opacity: local, transform: `translateX(${(1 - local) * (ci ? 40 : -40)}px)` }}>
                <div style={{ fontSize: T(vertical ? 30 : 32) * (vertical ? 1 : s), fontWeight: 800, color: ci ? theme.colors.accent : theme.colors.text_primary }}>
                  {col.title}
                </div>
                <div style={{ marginTop: 20, display: "flex", flexDirection: "column", gap: 14 }}>
                  {(col.items ?? []).map((it: string, i: number) => (
                    <div key={i} style={{ fontSize: T(vertical ? 27 : 26) * (vertical ? 1 : s), color: theme.colors.text_secondary, lineHeight: 1.5 }}>
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
                <div style={{ fontSize: T(vertical ? 30 : 34) * (vertical ? 1 : s), fontWeight: 800, color: theme.colors.text_primary }}>
                  {Math.round(d.value * grow)}
                </div>
                <div
                  style={{
                    width: vertical ? "86%" : "62%",
                    height: h,
                    background: negative
                      ? (theme.colors.warning ?? "#C98B5E")
                      : i === series.length - 1
                      ? theme.colors.accent
                      : theme.colors.surface,
                    borderRadius: 10,
                  }}
                />
                <div style={{ fontSize: T(vertical ? 22 : 25) * (vertical ? 1 : s), color: theme.colors.text_secondary }}>{d.label}</div>
              </div>
            );
          })}
        </div>
        {c.source ? (
          <div style={{ marginTop: 18, fontSize: T(vertical ? 18 : 20) * (vertical ? 1 : s), color: theme.colors.text_secondary, opacity: 0.7 }}>
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
            const local = spring({ frame: frame - Math.round(i * 0.16 * fps), fps, config: { damping: 200 }, durationInFrames: Math.round(0.36 * fps) });
            return (
              <div key={i} style={{ ...card(theme), flex: 1, opacity: local, transform: `translateY(${(1 - local) * 18}px)` }}>
                <div style={{ fontSize: T(vertical ? 20 : 22) * (vertical ? 1 : s), color: theme.colors.accent, fontWeight: 700 }}>{e.time}</div>
                <div style={{ ...heading(theme, (vertical ? 34 : 38) * (vertical ? 1 : s)), marginTop: 10 }}>{e.title}</div>
                {e.desc ? (
                  <div style={{ marginTop: 10, fontSize: T(vertical ? 21 : 23) * (vertical ? 1 : s), color: theme.colors.text_secondary, lineHeight: 1.5 }}>{e.desc}</div>
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
        <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", flexWrap: "wrap", gap: 24, flex: 1, justifyContent: "center" }}>
          {cards.map((cd, i) => {
            const local = spring({ frame: frame - Math.round(i * 0.14 * fps), fps, config: { damping: 160 }, durationInFrames: Math.round(0.32 * fps) });
            return (
              <div key={i} style={{ ...card(theme), flex: vertical ? "none" : "1 1 28%", opacity: local, transform: `scale(${0.94 + local * 0.06})` }}>
                <div style={{ ...heading(theme, (vertical ? 34 : 36) * (vertical ? 1 : s)) }}>{cd.title}</div>
                <div style={{ marginTop: 12, fontSize: T(vertical ? 24 : 24) * (vertical ? 1 : s), color: theme.colors.text_secondary, lineHeight: 1.55 }}>{cd.body}</div>
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
            const local = spring({ frame: frame - Math.round(i * 0.2 * fps), fps, config: { damping: 200 }, durationInFrames: Math.round(0.36 * fps) });
            return (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 18, opacity: local }}>
                <div style={{ ...card(theme), flex: 1, borderLeft: `4px solid ${theme.colors.accent}` }}>
                  <div style={{ fontSize: T(vertical ? 24 : 26) * (vertical ? 1 : s), color: theme.colors.text_primary }}>{row.cause}</div>
                </div>
                <div style={{ fontSize: T(30), color: theme.colors.accent }}>→</div>
                <div style={{ ...card(theme), flex: 1 }}>
                  <div style={{ fontSize: T(vertical ? 24 : 26) * (vertical ? 1 : s), color: theme.colors.text_secondary }}>{row.effect}</div>
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
          <div style={{ fontSize: T(vertical ? 34 : 40) * (vertical ? 1 : s), lineHeight: 1.6, color: theme.colors.text_primary }}>
            “{c.quote}”
          </div>
          <div style={{ marginTop: 26, fontSize: T(vertical ? 22 : 24) * (vertical ? 1 : s), color: theme.colors.accent }}>
            — {c.source}
          </div>
        </div>
      </AbsoluteFill>
    );
  }

  if (vt === "summary") {
    const points: string[] = c.points ?? [];
    return (
      <AbsoluteFill style={base}>
        {title}
        <div style={{ display: "flex", flexDirection: "column", gap: 26, flex: 1, justifyContent: "center" }}>
          {points.map((p, i) => {
            const local = spring({ frame: frame - Math.round(i * 0.16 * fps), fps, config: { damping: 200 }, durationInFrames: Math.round(0.36 * fps) });
            return (
              <div key={i} style={{ display: "flex", gap: 18, alignItems: "center", opacity: local, transform: `translateX(${(1 - local) * 24}px)` }}>
                <div style={{ color: theme.colors.accent, fontSize: T(vertical ? 32 : 32) * (vertical ? 1 : s), fontWeight: 800 }}>
                  {String(i + 1).padStart(2, "0")}
                </div>
                <div style={{ fontSize: T(vertical ? 40 : 34) * (vertical ? 1 : s), color: theme.colors.text_primary, lineHeight: 1.35 }}>{p}</div>
              </div>
            );
          })}
        </div>
        {c.conclusion ? (
          <div style={{ marginTop: 40, marginBottom: 70, fontSize: T(vertical ? 38 : 38) * (vertical ? 1 : s), fontWeight: 900, color: theme.colors.accent }}>
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
        <div style={{ fontSize: T(vertical ? 150 : 180) * (vertical ? 1 : s), fontWeight: 900, color: theme.colors.accent }}>
          {value}
          <span style={{ fontSize: T(48), marginLeft: 8, color: theme.colors.text_secondary }}>{c.unit ?? ""}</span>
        </div>
        {c.title ? (
          <div style={{ marginTop: 18, fontSize: T(vertical ? 30 : 32) * (vertical ? 1 : s), color: theme.colors.text_secondary }}>{c.title}</div>
        ) : null}
      </AbsoluteFill>
    );
  }

  // 兜底：标题 + 正文，保证任何 visual_type 都有可读画面
  return (
    <AbsoluteFill style={{ ...base, justifyContent: "center" }}>
      {title}
      <div style={{ fontSize: T(vertical ? 26 : 28) * (vertical ? 1 : s), color: theme.colors.text_secondary, lineHeight: 1.7, opacity: appear }}>
        {c.text ?? c.quote ?? ""}
      </div>
    </AbsoluteFill>
  );
};
