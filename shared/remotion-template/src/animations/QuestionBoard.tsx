import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { TEAM_COLORS } from "../data/segments";

// The big question: who's right? Shows competing philosophies
export const QuestionBoard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({ frame, fps, config: { damping: 14 }, durationInFrames: 25 });

  const questions = [
    { q: "Sidepods wash air outward or inward?", teams: ["Mercedes", "Red Bull"], delay: 1 },
    { q: "Wing opens from top or bottom?", teams: ["Alpine"], delay: 2 },
    { q: "Nose attaches to 1st or 2nd element?", teams: ["Mercedes", "Aston Martin"], delay: 3 },
    { q: "Suspension: grip or aero?", teams: ["Aston Martin", "Williams"], delay: 4 },
    { q: "Sidepod shape: invisible or wide?", teams: ["Red Bull", "Audi"], delay: 5 },
  ];

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      {/* Title */}
      <div
        style={{
          position: "absolute",
          top: 80,
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: interpolate(titleSpring, [0, 1], [0, 1]),
        }}
      >
        <div
          style={{
            fontFamily: "'Orbitron', sans-serif",
            fontSize: 48,
            fontWeight: 800,
            color: "white",
          }}
        >
          WHO'S RIGHT?
        </div>
        <div
          style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: 20,
            color: "rgba(255,255,255,0.4)",
            marginTop: 8,
          }}
        >
          Fundamental disagreements about basic physics
        </div>
      </div>

      {/* Question cards */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 20,
          marginTop: 60,
          maxWidth: 900,
          width: "100%",
          padding: "0 100px",
        }}
      >
        {questions.map((item, i) => {
          const cardSpring = spring({
            frame: frame - item.delay * fps,
            fps,
            config: { damping: 14 },
            durationInFrames: 25,
          });

          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 20,
                padding: "16px 24px",
                background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: 8,
                opacity: interpolate(cardSpring, [0, 1], [0, 1]),
                transform: `translateX(${interpolate(cardSpring, [0, 1], [-40, 0])}px)`,
              }}
            >
              {/* Question mark */}
              <div
                style={{
                  fontFamily: "'Orbitron', sans-serif",
                  fontSize: 24,
                  color: "#E10600",
                  fontWeight: 800,
                  minWidth: 30,
                }}
              >
                ?
              </div>

              {/* Question text */}
              <div style={{ flex: 1 }}>
                <div
                  style={{
                    fontFamily: "'Inter', sans-serif",
                    fontSize: 20,
                    color: "rgba(255,255,255,0.8)",
                  }}
                >
                  {item.q}
                </div>
              </div>

              {/* Team pills */}
              <div style={{ display: "flex", gap: 8 }}>
                {item.teams.map((team, j) => (
                  <div
                    key={j}
                    style={{
                      padding: "4px 12px",
                      background: `${TEAM_COLORS[team]?.primary || "#666"}22`,
                      border: `1px solid ${TEAM_COLORS[team]?.primary || "#666"}44`,
                      borderRadius: 20,
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: 11,
                      color: TEAM_COLORS[team]?.primary || "#666",
                      letterSpacing: 1,
                    }}
                  >
                    {team.toUpperCase()}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Warning */}
      <div
        style={{
          position: "absolute",
          bottom: 120,
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: interpolate(frame / fps, [8, 9], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        <div
          style={{
            fontFamily: "'Orbitron', sans-serif",
            fontSize: 22,
            color: "#E10600",
            fontWeight: 600,
          }}
        >
          At least 3-4 of them are going to be wrong.
        </div>
      </div>
    </AbsoluteFill>
  );
};
