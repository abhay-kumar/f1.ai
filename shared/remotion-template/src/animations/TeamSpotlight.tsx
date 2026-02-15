import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { TEAM_COLORS } from "../data/segments";

interface TeamSpotlightProps {
  team: string;
  carName?: string;
  headline?: string;
  stats?: { label: string; value: string }[];
  analogy?: string;
}

export const TeamSpotlight: React.FC<TeamSpotlightProps> = ({
  team,
  carName,
  headline,
  stats,
  analogy,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const colors = TEAM_COLORS[team] || { primary: "#E10600", accent: "#FFD700" };

  // Entrance springs
  const badgeSpring = spring({ frame, fps, config: { damping: 12 }, durationInFrames: 25 });
  const nameSpring = spring({ frame: frame - 10, fps, config: { damping: 14 }, durationInFrames: 25 });
  const headlineSpring = spring({ frame: frame - 20, fps, config: { damping: 15 }, durationInFrames: 25 });
  const statsSpring = spring({ frame: frame - 35, fps, config: { damping: 16 }, durationInFrames: 25 });
  const analogySpring = spring({ frame: frame - 50, fps, config: { damping: 16 }, durationInFrames: 25 });

  // Animated accent bar width
  const barWidth = interpolate(frame, [0, 40], [0, 400], {
    extrapolateRight: "clamp",
  });

  // Background pulse
  const glowRadius = interpolate(Math.sin(frame / 20), [-1, 1], [300, 500]);

  return (
    <AbsoluteFill>
      {/* Team color glow */}
      <div
        style={{
          position: "absolute",
          top: "30%",
          left: "20%",
          width: glowRadius,
          height: glowRadius,
          borderRadius: "50%",
          background: colors.primary,
          opacity: 0.06,
          filter: "blur(100px)",
        }}
      />

      {/* Content */}
      <div style={{ padding: "100px 100px", height: "100%", display: "flex", flexDirection: "column" }}>
        {/* Team badge */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 16,
            opacity: interpolate(badgeSpring, [0, 1], [0, 1]),
            transform: `translateX(${interpolate(badgeSpring, [0, 1], [-40, 0])}px)`,
          }}
        >
          <div
            style={{
              width: 8,
              height: 40,
              background: colors.primary,
              borderRadius: 4,
            }}
          />
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 18,
              letterSpacing: 4,
              color: colors.primary,
              textTransform: "uppercase",
            }}
          >
            {team}
          </div>
        </div>

        {/* Car name */}
        {carName && (
          <div
            style={{
              fontFamily: "'Orbitron', sans-serif",
              fontSize: 64,
              fontWeight: 800,
              color: "white",
              marginTop: 16,
              opacity: interpolate(nameSpring, [0, 1], [0, 1]),
              transform: `translateX(${interpolate(nameSpring, [0, 1], [-30, 0])}px)`,
              textShadow: `0 0 40px ${colors.primary}33`,
            }}
          >
            {carName}
          </div>
        )}

        {/* Accent bar */}
        <div
          style={{
            width: barWidth,
            height: 3,
            background: `linear-gradient(to right, ${colors.primary}, transparent)`,
            marginTop: 20,
            marginBottom: 24,
          }}
        />

        {/* Headline */}
        {headline && (
          <div
            style={{
              fontFamily: "'Inter', sans-serif",
              fontSize: 30,
              fontWeight: 300,
              color: "rgba(255,255,255,0.8)",
              maxWidth: 800,
              lineHeight: 1.4,
              opacity: interpolate(headlineSpring, [0, 1], [0, 1]),
              transform: `translateY(${interpolate(headlineSpring, [0, 1], [20, 0])}px)`,
            }}
          >
            {headline}
          </div>
        )}

        {/* Stats row */}
        {stats && stats.length > 0 && (
          <div
            style={{
              display: "flex",
              gap: 60,
              marginTop: 40,
              opacity: interpolate(statsSpring, [0, 1], [0, 1]),
              transform: `translateY(${interpolate(statsSpring, [0, 1], [20, 0])}px)`,
            }}
          >
            {stats.map((stat, i) => (
              <div key={i}>
                <div
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 13,
                    color: "rgba(255,255,255,0.4)",
                    letterSpacing: 2,
                    marginBottom: 6,
                  }}
                >
                  {stat.label}
                </div>
                <div
                  style={{
                    fontFamily: "'Orbitron', sans-serif",
                    fontSize: 28,
                    fontWeight: 700,
                    color: colors.primary,
                  }}
                >
                  {stat.value}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Spacer */}
        <div style={{ flex: 1 }} />

        {/* Analogy callout */}
        {analogy && (
          <div
            style={{
              padding: "20px 28px",
              background: "rgba(255,255,255,0.03)",
              borderLeft: `3px solid ${colors.primary}`,
              borderRadius: "0 8px 8px 0",
              maxWidth: 600,
              opacity: interpolate(analogySpring, [0, 1], [0, 1]),
              transform: `translateX(${interpolate(analogySpring, [0, 1], [-20, 0])}px)`,
              marginBottom: 100,
            }}
          >
            <div
              style={{
                fontFamily: "'Inter', sans-serif",
                fontSize: 20,
                fontStyle: "italic",
                color: "rgba(255,255,255,0.7)",
                lineHeight: 1.5,
              }}
            >
              "{analogy}"
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
