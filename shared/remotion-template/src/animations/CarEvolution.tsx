import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// Shows the evolution of F1 car diversity: 2000s wild variety → 2022 clones → 2026 chaos
export const CarEvolution: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const phaseTime = frame / fps;

  // Three eras with different car silhouettes
  const eras = [
    {
      year: "2000-2008",
      label: "THE WILD YEARS",
      subtitle: "Every race: new nose, new wing, new concept",
      diversity: 0.9,
      color: "#FFD700",
      carCount: 6,
    },
    {
      year: "2022-2025",
      label: "THE CLONE ERA",
      subtitle: "Ground-effect cars — variations on a theme",
      diversity: 0.2,
      color: "#666666",
      carCount: 6,
    },
    {
      year: "2026",
      label: "THE AERO ARMS RACE",
      subtitle: "10 teams, 10 completely different cars",
      diversity: 1.0,
      color: "#E10600",
      carCount: 8,
    },
  ];

  // Timeline position
  const currentEra = phaseTime < 12 ? Math.min(2, Math.floor(phaseTime / 4)) : 2;
  const eraProgress = phaseTime < 12
    ? (phaseTime % 4) / 4
    : 1;

  // Era transition
  const eraEntrance = spring({
    frame: frame - currentEra * 4 * fps,
    fps,
    config: { damping: 14 },
    durationInFrames: 30,
  });

  const era = eras[currentEra];

  // Generate varied car silhouettes based on diversity
  const cars = Array.from({ length: era.carCount }, (_, i) => {
    const baseWidth = 140;
    const variation = era.diversity;

    // Different nose heights, sidepod widths, wing angles per car
    const noseHeight = 40 + Math.sin(i * 2.3) * 15 * variation;
    const sidepodWidth = 30 + Math.cos(i * 1.7) * 12 * variation;
    const wingAngle = Math.sin(i * 3.1) * 20 * variation;
    const rearHeight = 35 + Math.sin(i * 1.1) * 10 * variation;

    return { noseHeight, sidepodWidth, wingAngle, rearHeight, baseWidth };
  });

  // Pulse animation for 2026 era
  const pulse = currentEra === 2
    ? interpolate(Math.sin(frame / 10), [-1, 1], [0.8, 1])
    : 1;

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      {/* Era label */}
      <div
        style={{
          position: "absolute",
          top: 100,
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: interpolate(eraEntrance, [0, 1], [0, 1]),
          transform: `translateY(${interpolate(eraEntrance, [0, 1], [-30, 0])}px)`,
        }}
      >
        <div
          style={{
            fontFamily: "'Orbitron', sans-serif",
            fontSize: 56,
            fontWeight: 800,
            color: era.color,
            textShadow: `0 0 30px ${era.color}44`,
          }}
        >
          {era.year}
        </div>
        <div
          style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: 28,
            fontWeight: 600,
            color: "white",
            marginTop: 8,
          }}
        >
          {era.label}
        </div>
        <div
          style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: 18,
            color: "rgba(255,255,255,0.5)",
            marginTop: 8,
          }}
        >
          {era.subtitle}
        </div>
      </div>

      {/* Car silhouettes grid */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: 30,
          maxWidth: 1200,
          marginTop: 60,
          transform: `scale(${pulse})`,
        }}
      >
        {cars.map((car, i) => {
          const carEntrance = spring({
            frame: frame - (currentEra * 4 * fps + i * 5),
            fps,
            config: { damping: 12 },
            durationInFrames: 20,
          });

          return (
            <div
              key={i}
              style={{
                opacity: interpolate(carEntrance, [0, 1], [0, 1]),
                transform: `translateY(${interpolate(carEntrance, [0, 1], [30, 0])}px)`,
              }}
            >
              <svg width={car.baseWidth} height={80} viewBox="0 0 140 80">
                {/* Car body */}
                <path
                  d={`M 20 ${car.noseHeight}
                      L 40 ${car.noseHeight - 10}
                      L 60 ${car.noseHeight - 15}
                      Q 80 ${car.noseHeight - 15 - car.sidepodWidth * 0.3}, 100 ${car.rearHeight}
                      L 120 ${car.rearHeight + 5}
                      L 120 55
                      L 20 55 Z`}
                  fill={era.color}
                  opacity={0.6 + i * 0.05}
                />
                {/* Front wing */}
                <line
                  x1="10"
                  y1="55"
                  x2="30"
                  y2={55 - Math.abs(car.wingAngle) * 0.3}
                  stroke={era.color}
                  strokeWidth={2.5}
                />
                {/* Rear wing */}
                <line
                  x1="115"
                  y1={car.rearHeight - 5}
                  x2="130"
                  y2={car.rearHeight - 5 + car.wingAngle * 0.2}
                  stroke={era.color}
                  strokeWidth={2.5}
                />
                {/* Wheels */}
                <circle cx="35" cy="58" r="8" fill="rgba(255,255,255,0.3)" />
                <circle cx="110" cy="58" r="8" fill="rgba(255,255,255,0.3)" />
              </svg>
            </div>
          );
        })}
      </div>

      {/* Diversity meter */}
      <div
        style={{
          position: "absolute",
          bottom: 180,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          gap: 20,
          opacity: interpolate(eraEntrance, [0, 1], [0, 1]),
        }}
      >
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 14,
            color: "rgba(255,255,255,0.5)",
            letterSpacing: 2,
          }}
        >
          DESIGN DIVERSITY
        </div>
        <div
          style={{
            width: 300,
            height: 8,
            background: "rgba(255,255,255,0.1)",
            borderRadius: 4,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: `${era.diversity * 100}%`,
              height: "100%",
              background: era.color,
              borderRadius: 4,
              boxShadow: `0 0 20px ${era.color}66`,
            }}
          />
        </div>
        <div
          style={{
            fontFamily: "'Orbitron', sans-serif",
            fontSize: 18,
            color: era.color,
          }}
        >
          {Math.round(era.diversity * 100)}%
        </div>
      </div>

      {/* Timeline dots at bottom */}
      <div
        style={{
          position: "absolute",
          bottom: 120,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          gap: 40,
        }}
      >
        {eras.map((e, i) => (
          <div key={i} style={{ textAlign: "center" }}>
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: "50%",
                background: i <= currentEra ? e.color : "rgba(255,255,255,0.2)",
                margin: "0 auto 8px auto",
                boxShadow: i === currentEra ? `0 0 15px ${e.color}` : "none",
              }}
            />
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 12,
                color: i === currentEra ? "white" : "rgba(255,255,255,0.3)",
              }}
            >
              {e.year}
            </div>
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
