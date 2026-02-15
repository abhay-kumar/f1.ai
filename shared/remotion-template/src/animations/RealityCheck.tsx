import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// Reality check: caveats about pre-season predictions
export const RealityCheck: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const phaseTime = frame / fps;
  const titleSpring = spring({ frame, fps, config: { damping: 14 }, durationInFrames: 25 });

  const caveats = [
    { text: "Barcelona was behind closed doors", delay: 1 },
    { text: "Teams are still holding cards", delay: 2.5 },
    { text: "Development hasn't even started", delay: 4 },
    { text: "Already matching 2025 pace", delay: 5.5 },
  ];

  // Warning pulse
  const warningPulse = interpolate(Math.sin(frame / 10), [-1, 1], [0.5, 1]);

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      {/* Title with warning */}
      <div
        style={{
          position: "absolute",
          top: 100,
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
            color: "#FFD700",
            opacity: warningPulse,
          }}
        >
          ⚠ REALITY CHECK
        </div>
        <div
          style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: 18,
            color: "rgba(255,255,255,0.4)",
            marginTop: 8,
          }}
        >
          Pre-season testing ≠ Season performance
        </div>
      </div>

      {/* Caveat list */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 16,
          maxWidth: 700,
          marginTop: 40,
        }}
      >
        {caveats.map((c, i) => {
          const itemSpring = spring({
            frame: frame - c.delay * fps,
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
                gap: 16,
                padding: "16px 24px",
                background: "rgba(255,215,0,0.03)",
                border: "1px solid rgba(255,215,0,0.1)",
                borderRadius: 8,
                opacity: interpolate(itemSpring, [0, 1], [0, 1]),
                transform: `translateX(${interpolate(itemSpring, [0, 1], [-30, 0])}px)`,
              }}
            >
              <div
                style={{
                  fontFamily: "'Orbitron', sans-serif",
                  fontSize: 18,
                  color: "#FFD700",
                  minWidth: 24,
                }}
              >
                {i + 1}
              </div>
              <div
                style={{
                  fontFamily: "'Inter', sans-serif",
                  fontSize: 20,
                  color: "rgba(255,255,255,0.7)",
                }}
              >
                {c.text}
              </div>
            </div>
          );
        })}
      </div>

      {/* Fun closer */}
      <div
        style={{
          position: "absolute",
          bottom: 120,
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: interpolate(phaseTime, [8, 9], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        <div
          style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: 20,
            fontStyle: "italic",
            color: "rgba(255,255,255,0.6)",
          }}
        >
          "Making wrong predictions and arguing about them on the internet
          <br />
          is half the fun of being an F1 fan."
        </div>
      </div>
    </AbsoluteFill>
  );
};
