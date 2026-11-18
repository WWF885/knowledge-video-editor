import { ThemeConfig, VideoProps } from "./components/theme";

/** Studio 预览用的最小示例。正式渲染由 scripts/render_video.py 通过 --props 注入。 */
const theme: ThemeConfig = {
  id: "dark_gold",
  name: "深空黑金",
  colors: {
    background: "#101820",
    surface: "#26323E",
    accent: "#D5B477",
    text_primary: "#F6F3EC",
    text_secondary: "#9AA9B6",
    divider: "rgba(246,243,236,0.12)",
  },
  typography: {
    font_family: "Source Han Sans SC, Noto Sans SC, PingFang SC, sans-serif",
    title_px: { horizontal: 132, vertical: 104 },
    chapter_px: { horizontal: 72, vertical: 68 },
    point_px: { horizontal: 52, vertical: 46 },
    body_px: { horizontal: 32, vertical: 30 },
    caption_px: { horizontal: 22, vertical: 20 },
    subtitle_zh_px: { horizontal: 54, vertical: 50 },
    subtitle_en_px: { horizontal: 34, vertical: 31 },
  },
};

const layout = {
  id: "horizontal",
  aspect_ratio: "16:9",
  resolution: [1920, 1080],
};

export const defaultProps: VideoProps = {
  storyboard: {
    video_type: "knowledge",
    aspect_ratio: "16:9",
    resolution: [1920, 1080],
    theme: "dark_gold",
    fps: 30,
    duration: 12,
    cover: { lines: ["工作方式", "彻底变了"], duration: 2, emphasis_index: 1, visible_from_first_frame: true },
    navigation: { enabled: true, chapters: ["现状", "逻辑", "案例", "总结"], height_ratio: 0.07 },
    subtitles: { languages: ["zh", "en"], layout: "chinese_above_english", safe_area_check: true },
    storyboard: [
      { scene_id: "S001", start: 0, end: 2, chapter: "现状", visual_type: "cover", content: { title_lines: ["工作方式", "彻底变了"] }, cover_visible: true, animation_plan: [{ time: 0, action: "cover_static" }] },
      { scene_id: "S002", start: 2, end: 7, chapter: "现状", visual_type: "presenter", content: { focus: "开场陈述" }, cover_visible: false, animation_plan: [{ time: 2, action: "show_navigation" }, { time: 4, action: "subtle_zoom" }] },
      { scene_id: "S003", start: 7, end: 12, chapter: "逻辑", visual_type: "flow_steps", content: { title: "三步复用", nodes: ["沉出方法", "换成产品", "持续交付"] }, cover_visible: false, animation_plan: [{ time: 7, action: "nodes_in" }, { time: 9, action: "connect_line" }] },
    ],
  },
  theme,
  layout,
  safeAreas: {},
  subtitles: {
    items: [
      { id: "sub_0001", start: 2, end: 4.5, zh: "真正改变的是工作方式", en: "What really changes is how we work." },
      { id: "sub_0002", start: 4.5, end: 7, zh: "而大多数人还在用时间换钱", en: "Most people still trade time for money." },
    ],
  },
};
