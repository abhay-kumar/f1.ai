import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { TEAM_COLORS } from "../data/segments";

// Final sign-off: rapid-fire team callback with all team colors
export const TeamRecap: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const teams = [
    { name: "Aston Martin", tagline: "Miracle car, half the prep time", icon: "AM" },
    { name: "Mercedes", tagline: "Rising sidepods — again", icon: "ME" },
    { name: "Williams", tagline: "Hiding their homework", icon: "WI" },
    { name: "Alpine", tagline: "Flipping the script on rear wings", icon: "AL" },
    { name: "Audi", tagline: "A car nobody recognized", icon: "AU" },
    { name: "McLaren", tagline: "Beautiful things with the floor", icon: "MC" },
    { name: "Red Bull", tagline: "Vacuum-sealed rear end", icon: "RB" },
    { name: "Ferrari", tagline: "Testing new tech in the rain", icon: "FE" },
  ];

  // Each team gets ~3 seconds of spotlight
  const teamDuration = 3; // seconds per team card
  const activeTeamIdx = Math.min(
    teams.length - 1,
    Math.floor((frame / fps) / teamDuration)
  );

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      {/* Title */}
      <div
        style={{
          position: "absolute",
          top: 60,
          left: 0,
          right: 0,
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontFamily: "'Orbitron', sans-serif",
            fontSize: 32,
            fontWeight: 700,
            color: "white",
          }}
        >
          THE 2026 GRID
        </div>
      </div>

      {/* Team cards - 2x4 grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: 16,
          maxWidth: 1400,
          padding: "0 60px",
          marginTop: 20,
        }}
      >
        {teams.map((team, i) => {
          const colors = TEAM_COLORS[team.name] || { primary: "#666", accent: "#999" };
          const isActive = i === activeTeamIdx;
          const isPast = i < activeTeamIdx;

          const cardSpring = spring({
            frame: frame - i * 0.5 * fps,
            fps,
            config: { damping: 14 },
            durationInFrames: 20,
          });

          const glowPulse = isActive
            ? interpolate(Math.sin(frame / 8), [-1, 1], [0.6, 1])
            : 0;

          return (
            <div
              key={i}
              style={{
                padding: "20px",
                background: isActive
                  ? `${colors.primary}15`
                  : "rgba(255,255,255,0.02)",
                border: `1px solid ${isActive ? colors.primary : "rgba(255,255,255,0.06)"}`,
                borderRadius: 10,
                opacity: interpolate(cardSpring, [0, 1], [0, 1]),
                transform: `scale(${isActive ? 1.02 : 1}) translateY(${interpolate(cardSpring, [0, 1], [20, 0])}px)`,
                boxShadow: isActive
                  ? `0 0 30px ${colors.primary}${Math.round(glowPulse * 30).toString(16).padStart(2, "0")}`
                  : "none",
                position: "relative",
              }}
            >
              {/* Team color bar */}
              <div
                style={{
                  width: "100%",
                  height: 3,
                  background: colors.primary,
                  borderRadius: 2,
                  marginBottom: 12,
                  opacity: isPast || isActive ? 1 : 0.3,
                }}
              />

              {/* Team icon */}
              <div
                style={{
                  fontFamily: "'Orbitron', sans-serif",
                  fontSize: 22,
                  fontWeight: 800,
                  color: colors.primary,
                  marginBottom: 8,
                }}
              >
                {team.icon}
              </div>

              {/* Team name */}
              <div
                style={{
                  fontFamily: "'Inter', sans-serif",
                  fontSize: 16,
                  fontWeight: 600,
                  color: isActive ? "white" : "rgba(255,255,255,0.6)",
                  marginBottom: 6,
                }}
              >
                {team.name}
              </div>

              {/* Tagline */}
              <div
                style={{
                  fontFamily: "'Inter', sans-serif",
                  fontSize: 13,
                  color: isActive ? "rgba(255,255,255,0.7)" : "rgba(255,255,255,0.35)",
                  lineHeight: 1.3,
                }}
              >
                {team.tagline}
              </div>

              {/* Check mark for past teams */}
              {isPast && (
                <div
                  style={{
                    position: "absolute",
                    top: 12,
                    right: 12,
                    width: 20,
                    height: 20,
                    borderRadius: "50%",
                    background: `${colors.primary}33`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 12,
                    color: colors.primary,
                  }}
                >
                  ✓
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Sign-off message */}
      <div
        style={{
          position: "absolute",
          bottom: 80,
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: interpolate(frame / fps, [teams.length * teamDuration - 5, teams.length * teamDuration - 3], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        <div
          style={{
            fontFamily: "'Orbitron', sans-serif",
            fontSize: 20,
            color: "#E10600",
            letterSpacing: 3,
          }}
        >
          F1 BURNOUTS
        </div>
        <div
          style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: 16,
            color: "rgba(255,255,255,0.4)",
            marginTop: 8,
          }}
        >
          Keep the rubber on the track, and the downforce where it belongs
        </div>
      </div>
    </AbsoluteFill>
  );
};
