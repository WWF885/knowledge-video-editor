import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig } from "remotion";
import { Cover } from "./components/Cover";
import { Navigation } from "./components/Navigation";
import { PresenterFrame } from "./components/PresenterFrame";
import { SubtitleLine } from "./components/Subtitles";
import { VisualScene } from "./components/VisualScene";
import { Scene, VideoProps } from "./components/theme";

const sceneComponent = (
  scene: Scene,
  props: VideoProps,
  vertical: boolean
): React.ReactNode => {
  if (scene.visual_type === "cover") {
    return (
      <Cover
        theme={props.theme}
        lines={scene.content?.title_lines ?? props.storyboard.cover.lines}
        emphasisIndex={props.storyboard.cover.emphasis_index ?? 1}
        vertical={vertical}
      />
    );
  }
  if (scene.visual_type === "presenter" || scene.visual_type === "presenter_pip") {
    return (
      <PresenterFrame
        scene={scene}
        theme={props.theme}
        layout={props.layout}
        presenterVideo={props.presenterVideo}
        vertical={vertical}
      />
    );
  }
  return <VisualScene scene={scene} theme={props.theme} layout={props.layout} vertical={vertical} />;
};

export const KnowledgeVideo: React.FC<VideoProps> = (props) => {
  const sb = props.storyboard;
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  const vertical = sb.aspect_ratio === "9:16";
  const t = frame / fps;

  const coverEnd = sb.storyboard[0]?.end ?? sb.cover.duration ?? 2;
  const navEnabled = Boolean(sb.navigation?.enabled);
  const showNav = navEnabled && t >= coverEnd + 0.3;

  const activeScene = sb.storyboard.find((s) => t >= s.start && t < s.end) ?? sb.storyboard[sb.storyboard.length - 1];
  const chapters = sb.navigation?.chapters ?? [];
  const activeIdx = Math.max(0, chapters.indexOf(activeScene?.chapter ?? chapters[0]));

  const subs = props.subtitles?.items ?? [];

  return (
    <AbsoluteFill style={{ backgroundColor: props.theme.colors.background }}>
      {sb.storyboard.map((scene) => {
        const from = Math.round(scene.start * fps);
        const dur = Math.max(1, Math.round((scene.end - scene.start) * fps));
        return (
          <Sequence key={scene.scene_id} from={from} durationInFrames={dur} name={scene.scene_id}>
            {sceneComponent(scene, props, vertical)}
          </Sequence>
        );
      })}

      {showNav && chapters.length >= 3 ? (
        <Sequence from={0} durationInFrames={Number.MAX_SAFE_INTEGER}>
          <Navigation
            theme={props.theme}
            chapters={chapters}
            activeIndex={Math.min(activeIdx, chapters.length - 1)}
            layout={props.layout}
            vertical={vertical}
          />
        </Sequence>
      ) : null}

      {subs.map((item) => {
        const from = Math.round(item.start * fps);
        const dur = Math.max(1, Math.round((item.end - item.start) * fps) + Math.round(0.15 * fps));
        return (
          <Sequence key={item.id} from={from} durationInFrames={dur} name={item.id}>
            <SubtitleLine item={item} theme={props.theme} layout={props.layout} vertical={vertical} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
