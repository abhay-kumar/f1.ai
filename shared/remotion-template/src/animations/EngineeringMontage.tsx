import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { TEAM_COLORS } from "../data/segments";

// Heartfelt segment: the human element behind the engineering
export const EngineeringMontage: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const phaseTime = frame / fps;

  const vignettes = [
    { text: "Thousands of simulations", icon: "▦", color: "#27F4D2", delay: 0 },
    { text: "3 AM ideas", icon: "◐", color: "#FFD700", delay: 1.5 },
    { text: "Sketching by hand", icon: "✎", color: TEAM_COLORS["Aston Martin"].primary, delay: 3 },
    { text: "Hidden from the world", icon: "◉", color: TEAM_COLORS.Williams.primary, delay: 4.5 },
    { text: "What if we flip it?", icon: "↻", color: TEAM_COLORS.Alpine.primary, delay: 6 },
  ];

  // Central quote reveal
  const quoteReveal = interpolate(phaseTime, [10, 12], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Floating carbon fiber particles
  const carbonParticles = Array.from({ length: 20 }, (_, i) => {
    const x = 50 + (i * 97) % 1800;
    const y = ((frame * 0.3 + i * 54) % 1100) - 50;
    const rotation = frame * 0.5 + i * 30;
    const opacity = interpolate(Math.sin(frame / 20 + i), [-1, 1], [0.02, 0.06]);
    return { x, y, rotation, opacity };
  });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      {/* Floating carbon fiber shapes */}
      <AbsoluteFill>
        {carbonParticles.map((p, i) => (
          <div
            key={i}
            style={{
              position: "absolute",
              left: p.x,
              top: p.y,
              width: 40,
              height: 3,
              background: "white",
              opacity: p.opacity,
              transform: `rotate(${p.rotation}deg)`,
              borderRadius: 2,
            }}
          />
        ))}
      </AbsoluteFill>

      {/* Title */}
      <div
        style={{
          position: "absolute",
          top: 100,
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: interpolate(
            spring({ frame, fps, config: { damping: 14 }, durationInFrames: 25 }),
            [0, 1],
            [0, 1]
          ),
        }}
      >
        <div
          style={{
            fontFamily: "'Orbitron', sans-serif",
            fontSize: 36,
            fontWeight: 700,
            color: "white",
            letterSpacing: 3,
          }}
        >
          THE HUMAN ELEMENT
        </div>
      </div>

      {/* Vignette cards */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: 24,
          maxWidth: 1200,
          marginTop: 40,
        }}
      >
        {vignettes.map((v, i) => {
          const cardSpring = spring({
            frame: frame - v.delay * fps,
            fps,
            config: { damping: 14 },
            durationInFrames: 30,
          });

          const pulse = interpolate(
            Math.sin(frame / 15 + i * 2),
            [-1, 1],
            [0.7, 1]
          );

          return (
            <div
              key={i}
              style={{
                width: 200,
                padding: "28px 20px",
                background: "rgba(255,255,255,0.02)",
                border: `1px solid ${v.color}22`,
                borderRadius: 12,
                textAlign: "center",
                opacity: interpolate(cardSpring, [0, 1], [0, 1]),
                transform: `translateY(${interpolate(cardSpring, [0, 1], [30, 0])}px) scale(${pulse})`,
              }}
            >
              <div
                style={{
                  fontSize: 36,
                  marginBottom: 16,
                  color: v.color,
                  opacity: 0.8,
                }}
              >
                {v.icon}
              </div>
              <div
                style={{
                  fontFamily: "'Inter', sans-serif",
                  fontSize: 16,
                  color: "rgba(255,255,255,0.7)",
                  lineHeight: 1.4,
                }}
              >
                {v.text}
              </div>
            </div>
          );
        })}
      </div>

      {/* Central inspirational quote */}
      <div
        style={{
          position: "absolute",
          bottom: 140,
          left: 100,
          right: 100,
          textAlign: "center",
          opacity: quoteReveal,
          transform: `translateY(${interpolate(quoteReveal, [0, 1], [20, 0])}px)`,
        }}
      >
        <div
          style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: 24,
            fontWeight: 300,
            color: "rgba(255,255,255,0.8)",
            lineHeight: 1.6,
            maxWidth: 800,
            margin: "0 auto",
          }}
        >
          These aren't just carbon fiber shapes.
          <br />
          They're <span style={{ color: "#E10600", fontWeight: 600 }}>ideas</span>.
          They're <span style={{ color: "#FFD700", fontWeight: 600 }}>bets</span>.
          <br />
          They're thousands of hours of human creativity
          <br />
          shaped into something that goes{" "}
          <span style={{ color: "#27F4D2", fontWeight: 600 }}>200 mph</span>.
        </div>
      </div>
    </AbsoluteFill>
  );
};
