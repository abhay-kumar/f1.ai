import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface TopicCardProps {
  title: string;
  teamColor: string;
  duration: number;
}

export const TopicCard: React.FC<TopicCardProps> = ({
  title = "STORY TITLE",
  teamColor = "#E10600",
  duration = 0.8,
}) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const totalFrames = Math.ceil(duration * fps);
  const is4K = width >= 3840;
  const scale = is4K ? 2 : 1;

  // Timing
  const lineFrames = Math.ceil(fps * 0.15);
  const textStartFrame = Math.ceil(fps * 0.08);
  const fadeOutStart = totalFrames - Math.ceil(fps * 0.15);

  // Line expansion spring
  const lineSpring = spring({
    frame,
    fps,
    config: { damping: 18, stiffness: 150 },
    durationInFrames: lineFrames,
  });

  // Fade out
  const fadeOut = interpolate(frame, [fadeOutStart, totalFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Background fade in
  const bgOpacity = interpolate(frame, [0, 3], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Line dimensions
  const lineW = is4K ? 700 : 400;
  const lineH = is4K ? 5 : 3;
  const lineGap = is4K ? 80 : 50;
  const pipSize = is4K ? 8 : 5;
  const titleSize = is4K ? 52 : 32;

  // Character stagger for title
  const chars = title.split("");
  const charDelay = 0.8; // frames between each character

  return (
    <AbsoluteFill
      style={{
        backgroundColor: `rgba(17, 17, 17, ${bgOpacity})`,
        justifyContent: "center",
        alignItems: "center",
        opacity: fadeOut,
      }}
    >
      {/* Top accent line — scales from center */}
      <div
        style={{
          position: "absolute",
          top: `calc(50% - ${lineGap}px)`,
          left: "50%",
          transform: `translateX(-50%) scaleX(${lineSpring})`,
          width: lineW,
          height: lineH,
          background: `linear-gradient(to right, transparent, ${teamColor}, transparent)`,
        }}
      />

      {/* Top pips */}
      <div
        style={{
          position: "absolute",
          top: `calc(50% - ${lineGap}px - ${pipSize / 2 - lineH / 2}px)`,
          left: `calc(50% - ${lineW / 2}px - ${pipSize + 4 * scale}px)`,
          width: pipSize,
          height: pipSize,
          borderRadius: "50%",
          backgroundColor: teamColor,
          opacity: interpolate(
            frame,
            [lineFrames, lineFrames + 4],
            [0, 0.8],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          ),
        }}
      />
      <div
        style={{
          position: "absolute",
          top: `calc(50% - ${lineGap}px - ${pipSize / 2 - lineH / 2}px)`,
          right: `calc(50% - ${lineW / 2}px - ${pipSize + 4 * scale}px)`,
          width: pipSize,
          height: pipSize,
          borderRadius: "50%",
          backgroundColor: teamColor,
          opacity: interpolate(
            frame,
            [lineFrames, lineFrames + 4],
            [0, 0.8],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          ),
        }}
      />

      {/* Title with character stagger */}
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          fontFamily: "'Formula1', 'Orbitron', sans-serif",
          fontSize: titleSize,
          fontWeight: 700,
          letterSpacing: 2 * scale,
        }}
      >
        {chars.map((char, i) => {
          const charFrame = textStartFrame + i * charDelay;
          const charProgress = interpolate(
            frame,
            [charFrame, charFrame + 5],
            [0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );
          return (
            <span
              key={i}
              style={{
                color: "white",
                opacity: charProgress,
                transform: `translateY(${interpolate(charProgress, [0, 1], [12 * scale, 0])}px)`,
                display: "inline-block",
                whiteSpace: "pre",
              }}
            >
              {char}
            </span>
          );
        })}
      </div>

      {/* Bottom accent line — scales from center */}
      <div
        style={{
          position: "absolute",
          top: `calc(50% + ${lineGap}px)`,
          left: "50%",
          transform: `translateX(-50%) scaleX(${lineSpring})`,
          width: lineW,
          height: lineH,
          background: `linear-gradient(to right, transparent, ${teamColor}, transparent)`,
        }}
      />

      {/* Bottom pips */}
      <div
        style={{
          position: "absolute",
          top: `calc(50% + ${lineGap}px - ${pipSize / 2 - lineH / 2}px)`,
          left: `calc(50% - ${lineW / 2}px - ${pipSize + 4 * scale}px)`,
          width: pipSize,
          height: pipSize,
          borderRadius: "50%",
          backgroundColor: teamColor,
          opacity: interpolate(
            frame,
            [lineFrames, lineFrames + 4],
            [0, 0.8],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          ),
        }}
      />
      <div
        style={{
          position: "absolute",
          top: `calc(50% + ${lineGap}px - ${pipSize / 2 - lineH / 2}px)`,
          right: `calc(50% - ${lineW / 2}px - ${pipSize + 4 * scale}px)`,
          width: pipSize,
          height: pipSize,
          borderRadius: "50%",
          backgroundColor: teamColor,
          opacity: interpolate(
            frame,
            [lineFrames, lineFrames + 4],
            [0, 0.8],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          ),
        }}
      />
    </AbsoluteFill>
  );
};
