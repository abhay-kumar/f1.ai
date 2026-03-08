import React from "react";
import { Composition } from "remotion";
import { VideoComposition } from "./VideoComposition";
import { FPS, VIDEO_DURATION } from "./data/segments";
import { LowerThird } from "./overlays/LowerThird";
import { TopicCard } from "./overlays/TopicCard";
import { Outro } from "./overlays/Outro";

const defaultLowerThirdProps = {
  title: "STORY TITLE",
  teamColor: "#E10600",
  duration: 3.5,
};

const defaultTopicCardProps = {
  title: "STORY TITLE",
  teamColor: "#E10600",
  duration: 0.8,
};

const defaultOutroProps = {
  teamColor: "#E10600",
  duration: 5,
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* 1080p HD composition */}
      <Composition
        id="F1Video"
        component={VideoComposition}
        durationInFrames={Math.ceil(VIDEO_DURATION * FPS)}
        fps={FPS}
        width={1920}
        height={1080}
        defaultProps={{}}
      />

      {/* 4K composition */}
      <Composition
        id="F1Video4K"
        component={VideoComposition}
        durationInFrames={Math.ceil(VIDEO_DURATION * FPS)}
        fps={FPS}
        width={3840}
        height={2160}
        defaultProps={{}}
      />

      {/* Lower Third overlays (transparent background) */}
      <Composition
        id="LowerThird"
        component={LowerThird}
        width={1920}
        height={1080}
        fps={FPS}
        defaultProps={defaultLowerThirdProps}
        calculateMetadata={({ props }) => ({
          durationInFrames: Math.ceil((props.duration || 3.5) * FPS),
        })}
      />
      <Composition
        id="LowerThird4K"
        component={LowerThird}
        width={3840}
        height={2160}
        fps={FPS}
        defaultProps={defaultLowerThirdProps}
        calculateMetadata={({ props }) => ({
          durationInFrames: Math.ceil((props.duration || 3.5) * FPS),
        })}
      />

      {/* Topic Card transitions (opaque dark background) */}
      <Composition
        id="TopicCard"
        component={TopicCard}
        width={1920}
        height={1080}
        fps={FPS}
        defaultProps={defaultTopicCardProps}
        calculateMetadata={({ props }) => ({
          durationInFrames: Math.ceil((props.duration || 0.8) * FPS),
        })}
      />
      <Composition
        id="TopicCard4K"
        component={TopicCard}
        width={3840}
        height={2160}
        fps={FPS}
        defaultProps={defaultTopicCardProps}
        calculateMetadata={({ props }) => ({
          durationInFrames: Math.ceil((props.duration || 0.8) * FPS),
        })}
      />

      {/* Outro CTA (opaque dark background) */}
      <Composition
        id="Outro"
        component={Outro}
        width={1920}
        height={1080}
        fps={FPS}
        defaultProps={defaultOutroProps}
        calculateMetadata={({ props }) => ({
          durationInFrames: Math.ceil((props.duration || 5) * FPS),
        })}
      />
      <Composition
        id="Outro4K"
        component={Outro}
        width={3840}
        height={2160}
        fps={FPS}
        defaultProps={defaultOutroProps}
        calculateMetadata={({ props }) => ({
          durationInFrames: Math.ceil((props.duration || 5) * FPS),
        })}
      />
    </>
  );
};
