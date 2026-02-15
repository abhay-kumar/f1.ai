import React from "react";
import {
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface SubtitleBarProps {
  text: string;
  emotion?: string;
  teamColor?: string;
}

export const SubtitleBar: React.FC<SubtitleBarProps> = ({
  text,
  emotion,
  teamColor,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Clean display text (remove emotion markers)
  const cleanText = text
    .replace(/\[.*?\]/g, "")
    .replace(/\s+/g, " ")
    .trim();

  // Break into words for word-by-word reveal
  const words = cleanText.split(" ");
  const wordsPerSecond = 3.5; // reading speed
  const framesPerWord = fps / wordsPerSecond;

  // Slide up entrance
  const slideUp = spring({
    frame,
    fps,
    config: { damping: 20, stiffness: 100 },
    durationInFrames: 20,
  });

  const translateY = interpolate(slideUp, [0, 1], [40, 0]);
  const opacity = interpolate(slideUp, [0, 1], [0, 1]);

  const accentColor = teamColor || "#E10600";

  return (
    <div
      style={{
        position: "absolute",
        bottom: 80,
        left: 80,
        right: 80,
        transform: `translateY(${translateY}px)`,
        opacity,
      }}
    >
      {/* Accent line */}
      <div
        style={{
          width: interpolate(frame, [0, 30], [0, 120], {
            extrapolateRight: "clamp",
          }),
          height: 3,
          background: accentColor,
          marginBottom: 16,
          borderRadius: 2,
        }}
      />

      {/* Subtitle text with word reveal */}
      <div
        style={{
          fontFamily: "'Inter', sans-serif",
          fontSize: 32,
          lineHeight: 1.5,
          color: "#ffffff",
          textShadow: "0 2px 20px rgba(0,0,0,0.8)",
          maxWidth: "80%",
        }}
      >
        {words.map((word, i) => {
          const wordFrame = i * framesPerWord;
          const wordOpacity = interpolate(
            frame,
            [wordFrame, wordFrame + 8],
            [0.3, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );
          return (
            <span key={i} style={{ opacity: wordOpacity }}>
              {word}{" "}
            </span>
          );
        })}
      </div>

      {/* Emotion indicator */}
      {emotion && (
        <div
          style={{
            marginTop: 12,
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 14,
            color: accentColor,
            opacity: 0.6,
            textTransform: "uppercase",
            letterSpacing: 3,
          }}
        >
          {emotion}
        </div>
      )}
    </div>
  );
};
