import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// McLaren MCL40: Triangle-stacked floor elements
export const FloorTriangle: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const phaseTime = frame / fps;
  const titleSpring = spring({ frame, fps, config: { damping: 14 }, durationInFrames: 25 });

  // Stacking animation: elements appear one by one
  const element1 = spring({ frame: frame - 2 * fps, fps, config: { damping: 12 }, durationInFrames: 25 });
  const element2 = spring({ frame: frame - 3.5 * fps, fps, config: { damping: 12 }, durationInFrames: 25 });
  const element3 = spring({ frame: frame - 5 * fps, fps, config: { damping: 12 }, durationInFrames: 25 });

  // Air bouncer effect
  const bouncerActive = phaseTime > 7;
  const bounceFrame = bouncerActive ? frame - 7 * fps : 0;

  // Airflow particles being directed
  const particles = Array.from({ length: 18 }, (_, i) => {
    const speed = 1.5 + (i % 3) * 0.4;
    const x = ((frame * speed + i * 45) % 700) + 150;
    const baseY = 280;
    // Bouncer effect: air pushed upward near the floor elements
    const pushed = bouncerActive && x > 350 && x < 600;
    const pushAmount = pushed ? -40 - Math.sin((x - 350) / 50) * 20 : 0;
    return { x, y: baseY + pushAmount, opacity: pushed ? 0.7 : 0.3, pushed };
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
          <div style={{ width: 8, height: 40, background: "#FF8000", borderRadius: 4 }} />
          <div>
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 16,
                color: "#FF8000",
                letterSpacing: 4,
              }}
            >
              McLAREN MCL40
            </div>
            <div
              style={{
                fontFamily: "'Orbitron', sans-serif",
                fontSize: 36,
                fontWeight: 700,
                color: "white",
              }}
            >
              TRIANGLE FLOOR STACK
            </div>
          </div>
        </div>
      </div>

      <svg width="900" height="400" viewBox="0 0 900 400" style={{ marginTop: 30 }}>
        {/* Airflow particles */}
        {particles.map((p, i) => (
          <g key={i}>
            <circle cx={p.x} cy={p.y} r={2.5} fill={p.pushed ? "#FF8000" : "#27F4D2"} opacity={p.opacity} />
            {/* Direction arrows for pushed air */}
            {p.pushed && (
              <line
                x1={p.x}
                y1={p.y}
                x2={p.x}
                y2={p.y - 8}
                stroke="#FF8000"
                strokeWidth={1}
                opacity={0.4}
              />
            )}
          </g>
        ))}

        {/* Triangle formation - big one on top */}
        {/* Top element (largest) */}
        <g
          opacity={interpolate(element1, [0, 1], [0, 1])}
          transform={`translateY(${interpolate(element1, [0, 1], [-30, 0])})`}
        >
          <path
            d="M 350 180 L 550 180 L 540 200 L 360 200 Z"
            fill="rgba(255,128,0,0.2)"
            stroke="#FF8000"
            strokeWidth={2}
          />
          <text x="450" y="195" textAnchor="middle" fill="#FF8000" fontSize="11" fontFamily="'JetBrains Mono', monospace">
            PRIMARY
          </text>
        </g>

        {/* Bottom-left element */}
        <g
          opacity={interpolate(element2, [0, 1], [0, 1])}
          transform={`translateY(${interpolate(element2, [0, 1], [-20, 0])})`}
        >
          <path
            d="M 370 215 L 440 215 L 435 232 L 375 232 Z"
            fill="rgba(255,128,0,0.15)"
            stroke="#FF8000"
            strokeWidth={1.5}
          />
        </g>

        {/* Bottom-right element */}
        <g
          opacity={interpolate(element3, [0, 1], [0, 1])}
          transform={`translateY(${interpolate(element3, [0, 1], [-20, 0])})`}
        >
          <path
            d="M 460 215 L 530 215 L 525 232 L 465 232 Z"
            fill="rgba(255,128,0,0.15)"
            stroke="#FF8000"
            strokeWidth={1.5}
          />
        </g>

        {/* Triangle outline connecting them */}
        {element3 > 0.5 && (
          <path
            d="M 450 175 L 365 235 L 535 235 Z"
            fill="none"
            stroke="rgba(255,128,0,0.3)"
            strokeWidth={1}
            strokeDasharray="4,4"
            opacity={element3 - 0.5}
          />
        )}

        {/* Underfloor */}
        <line x1="300" y1="300" x2="600" y2="300" stroke="rgba(255,255,255,0.15)" strokeWidth={1} />
        <text x="450" y="320" textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize="12" fontFamily="'JetBrains Mono', monospace">
          UNDERFLOOR
        </text>

        {/* Diffuser receiving merged airstreams */}
        {bouncerActive && (
          <g opacity={interpolate(phaseTime, [7, 8], [0, 0.8], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}>
            {/* Two converging air streams */}
            <path
              d="M 350 250 Q 400 270, 450 280"
              fill="none"
              stroke="#47C7FC"
              strokeWidth={2}
              opacity={0.5}
            />
            <path
              d="M 550 250 Q 500 270, 450 280"
              fill="none"
              stroke="#47C7FC"
              strokeWidth={2}
              opacity={0.5}
            />
            {/* Diffuser pressure zone */}
            <ellipse cx="450" cy="290" rx="60" ry="15" fill="rgba(71,199,252,0.1)" stroke="#47C7FC" strokeWidth={1} />
            <text x="450" y="295" textAnchor="middle" fill="#47C7FC" fontSize="10" fontFamily="'JetBrains Mono', monospace">
              PRESSURE ZONE
            </text>
          </g>
        )}
      </svg>

      {/* Bouncer analogy */}
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
          opacity: interpolate(phaseTime, [6, 7], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        "Like an invisible bouncer at a nightclub, deciding what air gets in and what gets turned away"
      </div>
    </AbsoluteFill>
  );
};
