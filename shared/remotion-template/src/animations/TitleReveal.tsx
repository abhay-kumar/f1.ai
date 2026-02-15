import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export const TitleReveal: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Staggered reveals
  const logoSpring = spring({ frame, fps, config: { damping: 12 }, durationInFrames: 30 });
  const titleSpring = spring({ frame: frame - 15, fps, config: { damping: 14 }, durationInFrames: 30 });
  const subtitleSpring = spring({ frame: frame - 35, fps, config: { damping: 16 }, durationInFrames: 30 });
  const lineSpring = spring({ frame: frame - 25, fps, config: { damping: 20 }, durationInFrames: 25 });

  // Checkered flag pattern animation
  const flagOffset = interpolate(frame, [0, fps * 5], [0, 100], { extrapolateRight: "extend" });

  // Pulsing glow
  const glowIntensity = interpolate(Math.sin(frame / 15), [-1, 1], [20, 40]);

  // Speed lines
  const speedLines = Array.from({ length: 8 }, (_, i) => {
    const delay = i * 4;
    const progress = interpolate(frame - delay, [0, 25], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    return { y: 15 + i * 10, progress, opacity: 1 - progress };
  });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      {/* Animated checkered pattern in background */}
      <AbsoluteFill style={{ opacity: 0.04 }}>
        <svg width="100%" height="100%">
          <defs>
            <pattern
              id="checker"
              width="60"
              height="60"
              patternUnits="userSpaceOnUse"
              patternTransform={`translate(${flagOffset}, 0)`}
            >
              <rect width="30" height="30" fill="white" />
              <rect x="30" y="30" width="30" height="30" fill="white" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#checker)" />
        </svg>
      </AbsoluteFill>

      {/* Speed lines */}
      <AbsoluteFill>
        {speedLines.map((line, i) => (
          <div
            key={i}
            style={{
              position: "absolute",
              top: `${line.y}%`,
              left: 0,
              width: `${line.progress * 100}%`,
              height: 1,
              background: `linear-gradient(to right, transparent, rgba(225, 6, 0, ${line.opacity * 0.3}))`,
            }}
          />
        ))}
      </AbsoluteFill>

      {/* Main title block */}
      <div style={{ textAlign: "center", position: "relative" }}>
        {/* F1 BURNOUTS badge */}
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 22,
            letterSpacing: 8,
            color: "#E10600",
            opacity: interpolate(logoSpring, [0, 1], [0, 0.8]),
            transform: `translateY(${interpolate(logoSpring, [0, 1], [-30, 0])}px)`,
            marginBottom: 20,
          }}
        >
          F1 BURNOUTS
        </div>

        {/* Accent line */}
        <div
          style={{
            width: interpolate(lineSpring, [0, 1], [0, 600]),
            height: 2,
            background: "linear-gradient(to right, transparent, #E10600, transparent)",
            margin: "0 auto 30px auto",
          }}
        />

        {/* Main title */}
        <div
          style={{
            fontFamily: "'Orbitron', sans-serif",
            fontSize: 72,
            fontWeight: 800,
            color: "white",
            textTransform: "uppercase",
            lineHeight: 1.1,
            opacity: interpolate(titleSpring, [0, 1], [0, 1]),
            transform: `scale(${interpolate(titleSpring, [0, 1], [0.8, 1])})`,
            textShadow: `0 0 ${glowIntensity}px rgba(225, 6, 0, 0.4)`,
            maxWidth: 1200,
          }}
        >
          The Aero
          <br />
          <span style={{ color: "#E10600" }}>Arms Race</span>
        </div>

        {/* Subtitle */}
        <div
          style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: 28,
            fontWeight: 300,
            color: "rgba(255,255,255,0.7)",
            marginTop: 24,
            letterSpacing: 2,
            opacity: interpolate(subtitleSpring, [0, 1], [0, 1]),
            transform: `translateY(${interpolate(subtitleSpring, [0, 1], [20, 0])}px)`,
          }}
        >
          Every Team's Secret Weapon for 2026
        </div>

        {/* Year badge */}
        <div
          style={{
            marginTop: 40,
            display: "inline-block",
            padding: "8px 32px",
            border: "1px solid rgba(225, 6, 0, 0.4)",
            borderRadius: 4,
            fontFamily: "'Orbitron', sans-serif",
            fontSize: 18,
            color: "#E10600",
            letterSpacing: 6,
            opacity: interpolate(subtitleSpring, [0, 1], [0, 0.7]),
          }}
        >
          2026 SEASON
        </div>
      </div>
    </AbsoluteFill>
  );
};
