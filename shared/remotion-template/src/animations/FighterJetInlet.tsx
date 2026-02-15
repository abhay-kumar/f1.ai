import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// Audi B-spec: Fighter jet style narrow tall inlets with aggressive undercut
export const FighterJetInlet: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const phaseTime = frame / fps;
  const titleSpring = spring({ frame, fps, config: { damping: 14 }, durationInFrames: 25 });

  // Inlet air suction visualization
  const suctionPulse = interpolate(Math.sin(frame / 12), [-1, 1], [0.4, 1]);

  // Detail callouts appear sequentially
  const detail1 = spring({ frame: frame - 3 * fps, fps, config: { damping: 14 }, durationInFrames: 25 });
  const detail2 = spring({ frame: frame - 5 * fps, fps, config: { damping: 14 }, durationInFrames: 25 });
  const detail3 = spring({ frame: frame - 7 * fps, fps, config: { damping: 14 }, durationInFrames: 25 });

  // Air being channeled
  const flowParticles = Array.from({ length: 15 }, (_, i) => {
    const speed = 1.8 + (i % 4) * 0.3;
    const x = ((frame * speed + i * 40) % 600) + 200;
    const inInlet = x > 350 && x < 430;
    const pastInlet = x > 430;
    const y = inInlet
      ? interpolate(x, [350, 430], [200, 260])
      : pastInlet
        ? 260 + Math.sin((x - 430) / 40) * 15
        : 200 + Math.sin(i * 1.3) * 20;
    return { x, y, inInlet, opacity: inInlet ? 0.8 * suctionPulse : 0.3 };
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
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ width: 8, height: 40, background: "#E10600", borderRadius: 4 }} />
          <div>
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 16,
                color: "rgba(255,255,255,0.6)",
                letterSpacing: 4,
              }}
            >
              AUDI B-SPEC
            </div>
            <div
              style={{
                fontFamily: "'Orbitron', sans-serif",
                fontSize: 36,
                fontWeight: 700,
                color: "white",
              }}
            >
              FIGHTER JET ENGINEERING
            </div>
          </div>
        </div>
      </div>

      <svg width="900" height="400" viewBox="0 0 900 400" style={{ marginTop: 30 }}>
        {/* Car body */}
        <path
          d="M 250 230 L 320 210 Q 450 195, 580 210 L 650 230 L 650 290 L 250 290 Z"
          fill="rgba(255,255,255,0.04)"
          stroke="rgba(255,255,255,0.2)"
          strokeWidth={1.5}
        />

        {/* B-spec tall narrow inlet */}
        <rect
          x="370"
          y="175"
          width="25"
          height="70"
          rx="4"
          fill={`rgba(225,6,0,${0.1 + suctionPulse * 0.1})`}
          stroke="#E10600"
          strokeWidth={2}
        />

        {/* Aggressive undercut below */}
        <path
          d="M 395 250 Q 430 280, 500 270 L 500 285 Q 430 290, 395 285 Z"
          fill="rgba(225,6,0,0.08)"
          stroke="#E10600"
          strokeWidth={1.5}
        />

        {/* Air particles */}
        {flowParticles.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r={p.inInlet ? 3 : 2}
            fill={p.inInlet ? "#E10600" : "#27F4D2"}
            opacity={p.opacity}
          />
        ))}

        {/* Detail callout 1: Inlet */}
        <g opacity={interpolate(detail1, [0, 1], [0, 1])}>
          <line x1="383" y1="170" x2="300" y2="140" stroke="rgba(255,255,255,0.3)" strokeWidth={1} />
          <text x="295" y="130" textAnchor="end" fill="#E10600" fontSize="12" fontFamily="'JetBrains Mono', monospace">
            Narrow + tall inlet
          </text>
          <text x="295" y="145" textAnchor="end" fill="rgba(255,255,255,0.4)" fontSize="11" fontFamily="'Inter', sans-serif">
            Like fighter jet air scoops
          </text>
        </g>

        {/* Detail callout 2: Undercut */}
        <g opacity={interpolate(detail2, [0, 1], [0, 1])}>
          <line x1="450" y1="275" x2="550" y2="310" stroke="rgba(255,255,255,0.3)" strokeWidth={1} />
          <text x="555" y="310" fill="#E10600" fontSize="12" fontFamily="'JetBrains Mono', monospace">
            Aggressive undercut
          </text>
          <text x="555" y="325" fill="rgba(255,255,255,0.4)" fontSize="11" fontFamily="'Inter', sans-serif">
            Channels air to floor
          </text>
        </g>

        {/* Detail callout 3: Floor vane */}
        <g opacity={interpolate(detail3, [0, 1], [0, 1])}>
          <line x1="490" y1="285" x2="490" y2="320" stroke="#FFD700" strokeWidth={2} />
          <rect x="487" y="279" width="6" height="12" rx="1" fill="#FFD700" opacity={0.8} />
          <line x1="490" y1="325" x2="600" y2="350" stroke="rgba(255,255,255,0.3)" strokeWidth={1} />
          <text x="605" y="345" fill="#FFD700" fontSize="12" fontFamily="'JetBrains Mono', monospace">
            Tiny metal vane
          </text>
          <text x="605" y="360" fill="rgba(255,255,255,0.4)" fontSize="11" fontFamily="'Inter', sans-serif">
            Redirects air upward — nobody else has this
          </text>
        </g>

        {/* Wheels */}
        <circle cx="300" cy="295" r="20" fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth={2} />
        <circle cx="600" cy="295" r="20" fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth={2} />
      </svg>

      {/* Quote */}
      <div
        style={{
          position: "absolute",
          bottom: 100,
          left: 80,
          right: 80,
          textAlign: "center",
          fontFamily: "'Inter', sans-serif",
          fontSize: 18,
          fontStyle: "italic",
          color: "rgba(255,255,255,0.5)",
          opacity: interpolate(phaseTime, [9, 10], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        "You can't accuse them of playing it safe."
      </div>
    </AbsoluteFill>
  );
};
