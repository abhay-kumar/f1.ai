import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface BackgroundProps {
  teamColor?: string;
  teamAccent?: string;
  emotion?: string;
}

export const Background: React.FC<BackgroundProps> = ({
  teamColor,
  teamAccent,
  emotion,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const baseColor = teamColor || "#0a0a0a";
  const accent = teamAccent || "#E10600";

  // Slowly rotating gradient angle
  const angle = interpolate(frame, [0, fps * 30], [0, 360], {
    extrapolateRight: "extend",
  });

  // Pulsing grid opacity based on emotion
  const gridOpacity = emotion === "energetic" || emotion === "excited"
    ? interpolate(Math.sin(frame / 20), [-1, 1], [0.03, 0.08])
    : 0.04;

  // Floating particles
  const particles = Array.from({ length: 15 }, (_, i) => {
    const speed = 0.3 + (i * 0.1);
    const x = ((i * 137.5 + frame * speed * 0.5) % 120) - 10;
    const y = ((i * 89.3 + frame * speed * 0.3) % 120) - 10;
    const size = 2 + (i % 3) * 1.5;
    const opacity = interpolate(
      Math.sin(frame / (30 + i * 5) + i),
      [-1, 1],
      [0.05, 0.2]
    );
    return { x, y, size, opacity };
  });

  return (
    <AbsoluteFill>
      {/* Deep dark base */}
      <div
        style={{
          width: "100%",
          height: "100%",
          background: `
            radial-gradient(ellipse at 30% 20%, ${baseColor}33 0%, transparent 50%),
            radial-gradient(ellipse at 70% 80%, ${accent}22 0%, transparent 50%),
            linear-gradient(${angle}deg, #050505 0%, #0a0a0a 50%, #050505 100%)
          `,
        }}
      />

      {/* Racing grid lines */}
      <AbsoluteFill style={{ opacity: gridOpacity }}>
        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="grid" width="80" height="80" patternUnits="userSpaceOnUse">
              <path
                d="M 80 0 L 0 0 0 80"
                fill="none"
                stroke={accent}
                strokeWidth="0.5"
              />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </AbsoluteFill>

      {/* Floating particles */}
      <AbsoluteFill>
        {particles.map((p, i) => (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${p.x}%`,
              top: `${p.y}%`,
              width: p.size,
              height: p.size,
              borderRadius: "50%",
              background: i % 2 === 0 ? accent : baseColor,
              opacity: p.opacity,
              filter: "blur(1px)",
            }}
          />
        ))}
      </AbsoluteFill>

      {/* Edge vignette */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.7) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};
