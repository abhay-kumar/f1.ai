import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// Audi: Barcelona car morphs into Bahrain B-spec
export const AudiTransform: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const phaseTime = frame / fps;

  // Morph progress: 0 = A-spec, 1 = B-spec
  const morphProgress = interpolate(phaseTime, [4, 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const titleSpring = spring({ frame, fps, config: { damping: 14 }, durationInFrames: 25 });

  // Sidepod dimensions morph
  const sidepodWidth = interpolate(morphProgress, [0, 1], [120, 70]); // narrows
  const sidepodHeight = interpolate(morphProgress, [0, 1], [60, 90]); // taller
  const inletForward = interpolate(morphProgress, [0, 1], [0, 40]); // stretches forward
  const undercutDepth = interpolate(morphProgress, [0, 1], [10, 40]); // aggressive undercut

  // Flash at morph point
  const flashIntensity = interpolate(phaseTime, [5.5, 6, 6.5], [0, 0.15, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Airflow particles
  const flowParticles = Array.from({ length: 12 }, (_, i) => {
    const speed = 1.5 + (i % 3) * 0.5;
    const x = ((frame * speed + i * 50) % 800) + 100;
    const yBase = 250 + Math.sin(i * 2.1) * 40;
    // B-spec channels air more aggressively downward
    const channeling = morphProgress * 30 * (x > 400 && x < 600 ? 1 : 0);
    return { x, y: yBase + channeling, opacity: 0.4 };
  });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      {/* Title */}
      <div
        style={{
          position: "absolute",
          top: 80,
          left: 80,
          opacity: interpolate(titleSpring, [0, 1], [0, 1]),
        }}
      >
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 16,
            color: "#E10600",
            letterSpacing: 4,
          }}
        >
          AUDI
        </div>
        <div
          style={{
            fontFamily: "'Orbitron', sans-serif",
            fontSize: 36,
            fontWeight: 700,
            color: "white",
          }}
        >
          THE B-SPEC SURPRISE
        </div>
      </div>

      {/* Spec label */}
      <div
        style={{
          position: "absolute",
          top: 80,
          right: 80,
          textAlign: "right",
        }}
      >
        <div
          style={{
            fontFamily: "'Orbitron', sans-serif",
            fontSize: 48,
            fontWeight: 800,
            color: morphProgress < 0.5 ? "rgba(255,255,255,0.3)" : "#E10600",
          }}
        >
          {morphProgress < 0.5 ? "A-SPEC" : "B-SPEC"}
        </div>
        <div
          style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: 16,
            color: "rgba(255,255,255,0.4)",
          }}
        >
          {morphProgress < 0.5 ? "Barcelona Shakedown" : "Bahrain Pre-Season"}
        </div>
      </div>

      {/* Car side view with morphing sidepods */}
      <svg width="900" height="350" viewBox="0 0 900 350" style={{ marginTop: 30 }}>
        {/* Airflow */}
        {flowParticles.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r={2.5} fill="#27F4D2" opacity={p.opacity} />
        ))}

        {/* Car body base */}
        <path
          d="M 200 200 L 280 180 Q 400 170, 550 180 L 650 195 L 700 200 L 700 260 L 200 260 Z"
          fill="rgba(255,255,255,0.05)"
          stroke="rgba(255,255,255,0.2)"
          strokeWidth={1.5}
        />

        {/* Morphing sidepod inlet */}
        <rect
          x={350 - inletForward}
          y={180 - sidepodHeight * 0.3}
          width={sidepodWidth}
          height={sidepodHeight}
          rx={6}
          fill={morphProgress > 0.5 ? "rgba(225,6,0,0.15)" : "rgba(255,255,255,0.08)"}
          stroke={morphProgress > 0.5 ? "#E10600" : "rgba(255,255,255,0.3)"}
          strokeWidth={2}
        />

        {/* Undercut */}
        <path
          d={`M ${350 + sidepodWidth - inletForward} ${180 + sidepodHeight * 0.7}
              Q ${400 + sidepodWidth} ${180 + sidepodHeight * 0.7 + undercutDepth},
              ${450 + sidepodWidth} ${230}`}
          fill="none"
          stroke={morphProgress > 0.5 ? "#E10600" : "rgba(255,255,255,0.2)"}
          strokeWidth={2}
          strokeDasharray={morphProgress > 0.5 ? "none" : "4,4"}
        />

        {/* Fighter jet inlet label */}
        {morphProgress > 0.7 && (
          <g opacity={morphProgress - 0.7}>
            <line
              x1={340 - inletForward}
              y1={180}
              x2={280 - inletForward}
              y2={140}
              stroke="rgba(255,255,255,0.3)"
              strokeWidth={1}
            />
            <text
              x={275 - inletForward}
              y={135}
              textAnchor="end"
              fill="rgba(255,255,255,0.7)"
              fontSize="13"
              fontFamily="'JetBrains Mono', monospace"
            >
              Fighter jet inlets
            </text>
          </g>
        )}

        {/* Wheels */}
        <circle cx="280" cy="265" r="22" fill="none" stroke="rgba(255,255,255,0.3)" strokeWidth={2} />
        <circle cx="620" cy="265" r="22" fill="none" stroke="rgba(255,255,255,0.3)" strokeWidth={2} />

        {/* Ground */}
        <line x1="150" y1="290" x2="750" y2="290" stroke="rgba(255,255,255,0.1)" strokeWidth={1} />
      </svg>

      {/* Morph progress bar */}
      <div
        style={{
          position: "absolute",
          bottom: 200,
          left: 200,
          right: 200,
          display: "flex",
          alignItems: "center",
          gap: 20,
        }}
      >
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 12,
            color: "rgba(255,255,255,0.4)",
          }}
        >
          BARCELONA
        </div>
        <div
          style={{
            flex: 1,
            height: 4,
            background: "rgba(255,255,255,0.1)",
            borderRadius: 2,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: `${morphProgress * 100}%`,
              height: "100%",
              background: "linear-gradient(to right, rgba(255,255,255,0.3), #E10600)",
              borderRadius: 2,
            }}
          />
        </div>
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 12,
            color: morphProgress > 0.8 ? "#E10600" : "rgba(255,255,255,0.4)",
          }}
        >
          BAHRAIN
        </div>
      </div>

      {/* Flash overlay */}
      <AbsoluteFill
        style={{
          background: `rgba(225, 6, 0, ${flashIntensity})`,
          pointerEvents: "none",
        }}
      />

      {/* Quote */}
      <div
        style={{
          position: "absolute",
          bottom: 120,
          left: 80,
          right: 80,
          textAlign: "center",
          fontFamily: "'Inter', sans-serif",
          fontSize: 18,
          fontStyle: "italic",
          color: "rgba(255,255,255,0.5)",
          opacity: interpolate(phaseTime, [8, 9], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        "Like showing up to a second date having completely changed your hairstyle, wardrobe, and personality"
      </div>
    </AbsoluteFill>
  );
};
