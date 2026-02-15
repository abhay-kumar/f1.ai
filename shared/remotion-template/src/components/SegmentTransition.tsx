import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface SegmentTransitionProps {
  teamColor?: string;
  direction?: "in" | "out";
  durationFrames?: number;
}

export const SegmentTransition: React.FC<SegmentTransitionProps> = ({
  teamColor = "#E10600",
  direction = "in",
  durationFrames = 15,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame,
    fps,
    config: { damping: 20, stiffness: 120 },
    durationInFrames: durationFrames,
  });

  if (direction === "in") {
    // Wipe in from left with team color accent
    const wipeWidth = interpolate(progress, [0, 0.5, 1], [0, 100, 0]);
    const wipeX = interpolate(progress, [0, 1], [-10, 110]);

    return (
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <div
          style={{
            position: "absolute",
            left: `${wipeX - wipeWidth}%`,
            top: 0,
            width: `${wipeWidth}%`,
            height: "100%",
            background: `linear-gradient(to right, transparent, ${teamColor}33, ${teamColor}22, transparent)`,
          }}
        />
        {/* Thin accent line */}
        <div
          style={{
            position: "absolute",
            left: `${wipeX}%`,
            top: 0,
            width: 2,
            height: "100%",
            background: teamColor,
            opacity: interpolate(progress, [0, 0.5, 1], [0, 0.6, 0]),
          }}
        />
      </AbsoluteFill>
    );
  }

  // Fade out
  const fadeOpacity = interpolate(progress, [0, 1], [0, 0.3]);
  return (
    <AbsoluteFill
      style={{
        background: `rgba(0,0,0,${fadeOpacity})`,
        pointerEvents: "none",
      }}
    />
  );
};
