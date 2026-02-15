import React from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
  staticFile,
  useVideoConfig,
} from "remotion";
import { segments } from "./data/segments";
import { SegmentRenderer } from "./components/SegmentRenderer";
import "./style.css";

// =============================================================================
// MAIN VIDEO COMPOSITION
// =============================================================================
// This is the top-level component that:
//   1. Plays the full audio track (synced to video)
//   2. Renders each segment as a timed Sequence
//   3. Each Sequence contains a SegmentRenderer with the right animation
//
// SETUP:
//   - Place your concatenated audio file in public/audio.mp3
//   - Define segments in src/data/segments.ts with VTT timestamps
//   - Wire up animations in src/components/SegmentRenderer.tsx
// =============================================================================

export const VideoComposition: React.FC = () => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#050505" }}>
      {/* Full audio track — place your audio in public/audio.mp3 */}
      <Audio src={staticFile("audio.mp3")} />

      {/* Render each segment as a timed Sequence */}
      {segments.map((segment) => {
        const startFrame = Math.round(segment.startTime * fps);
        const durationFrames = Math.round(
          (segment.endTime - segment.startTime) * fps
        );

        return (
          <Sequence
            key={segment.id}
            from={startFrame}
            durationInFrames={durationFrames}
            name={`Seg ${segment.id}: ${segment.context}`}
          >
            <SegmentRenderer segment={segment} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
