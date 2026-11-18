import { Composition } from "remotion";
import React from "react";
import { KnowledgeVideo } from "./Video";
import { defaultProps } from "./defaultProps";
import { VideoProps } from "./components/theme";

const durationOf = (p: VideoProps) => {
  const sb = p.storyboard;
  const end = sb.duration ?? sb.storyboard[sb.storyboard.length - 1]?.end ?? 10;
  return Math.max(1, Math.ceil(end * (sb.fps ?? 30)));
};

export const RemotionRoot: React.FC = () => (
  <Composition
    id="KnowledgeVideo"
    component={KnowledgeVideo}
    defaultProps={defaultProps}
    durationInFrames={durationOf(defaultProps)}
    fps={defaultProps.storyboard.fps ?? 30}
    width={1920}
    height={1080}
    calculateMetadata={({ props }) => {
      const p = props as unknown as VideoProps;
      const res = p.layout?.resolution ?? p.storyboard.resolution ?? [1920, 1080];
      return {
        durationInFrames: durationOf(p),
        fps: p.storyboard.fps ?? 30,
        width: res[0],
        height: res[1],
      };
    }}
  />
);
