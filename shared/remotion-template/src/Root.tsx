import React from "react";
import { Composition } from "remotion";
import { VideoComposition } from "./VideoComposition";
import { FPS, VIDEO_DURATION } from "./data/segments";

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
    </>
  );
};
