export type ThemeConfig = {
  id: string;
  name: string;
  colors: {
    background: string;
    surface: string;
    deep?: string;
    accent: string;
    text_primary: string;
    text_secondary: string;
    success?: string;
    warning?: string;
    divider?: string;
  };
  typography: {
    font_family: string;
    title_px: { horizontal: number; vertical: number };
    chapter_px: { horizontal: number; vertical: number };
    point_px: { horizontal: number; vertical: number };
    body_px: { horizontal: number; vertical: number };
    caption_px: { horizontal: number; vertical: number };
    subtitle_zh_px: { horizontal: number; vertical: number };
    subtitle_en_px: { horizontal: number; vertical: number };
  };
};

export type Scene = {
  scene_id: string;
  start: number;
  end: number;
  chapter?: string;
  visual_type: string;
  layout?: Record<string, any>;
  content?: Record<string, any>;
  cover_visible?: boolean;
  animation_plan?: Array<{ time: number; action: string; ease?: string; dur?: number; target?: any }>;
  sfx?: Array<{ at: number; name: string; gain?: number }>;
  subtitle_ref?: string[];
};

export type Storyboard = {
  video_type: string;
  aspect_ratio: string;
  resolution: [number, number];
  theme: string;
  fps?: number;
  duration?: number;
  cover: {
    lines: string[];
    duration?: number;
    emphasis_index?: number;
    visible_from_first_frame?: boolean;
  };
  navigation: { enabled: boolean; chapters: string[]; height_ratio?: number; hide_during_cover?: boolean };
  subtitles: { languages: string[]; layout: string; safe_area_check?: boolean };
  storyboard: Scene[];
};

export type SubItem = { id: string; start: number; end: number; zh: string; en?: string };

export type VideoProps = {
  storyboard: Storyboard;
  theme: ThemeConfig;
  layout: any;
  safeAreas: any;
  subtitles?: { items: SubItem[] };
  presenterVideo?: string;
  bgm?: string;
};

export const fontOf = (t: ThemeConfig) =>
  t.typography.font_family || "Source Han Sans SC, Noto Sans SC, sans-serif";

export const scaleFor = (layout: any) => {
  const width = layout?.resolution?.[0] ?? 1920;
  return width / 1920;
};
