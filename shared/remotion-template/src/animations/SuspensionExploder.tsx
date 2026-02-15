import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// Aston Martin: Suspension arms explode outward to show dual-purpose aero + structure
export const SuspensionExploder: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const phaseTime = frame / fps;

  // Phase: assembled (0-5s) → explode (5-10s) → airflow reveal (10s+)
  const explodeProgress = interpolate(phaseTime, [5, 9], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const airflowReveal = interpolate(phaseTime, [10, 12], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Suspension components
  const parts = [
    { name: "Upper Wishbone", x: 500, y: 280, explodeX: -120, explodeY: -80, width: 160, angle: -15, color: "#CEDC00" },
    { name: "Lower Wishbone", x: 500, y: 360, explodeX: -120, explodeY: 80, width: 160, angle: 10, color: "#CEDC00" },
    { name: "Pushrod", x: 560, y: 320, explodeX: 0, explodeY: -120, width: 100, angle: -60, color: "#006F62" },
    { name: "Track Rod", x: 480, y: 340, explodeX: -160, explodeY: 0, width: 120, angle: -5, color: "#006F62" },
    { name: "Anti-Roll Bar", x: 540, y: 300, explodeX: 120, explodeY: -100, width: 80, angle: 0, color: "#CEDC00" },
  ];

  // Label entrance
  const labelSpring = spring({ frame: frame - 5 * fps, fps, config: { damping: 15 } });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      {/* Title */}
      <div
        style={{
          position: "absolute",
          top: 80,
          left: 80,
          display: "flex",
          alignItems: "center",
          gap: 16,
        }}
      >
        <div style={{ width: 8, height: 40, background: "#006F62", borderRadius: 4 }} />
        <div>
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 16,
              color: "#006F62",
              letterSpacing: 4,
            }}
          >
            ASTON MARTIN AMR26
          </div>
          <div
            style={{
              fontFamily: "'Orbitron', sans-serif",
              fontSize: 36,
              fontWeight: 700,
              color: "white",
            }}
          >
            SUSPENSION AS AERO
          </div>
        </div>
      </div>

      <svg width="1200" height="600" viewBox="0 0 1200 600" style={{ marginTop: 20 }}>
        {/* Wheel hub (static reference) */}
        <circle cx="700" cy="320" r="50" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth={2} />
        <circle cx="700" cy="320" r="35" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth={1} />

        {/* Chassis reference */}
        <rect
          x="350"
          y="260"
          width="200"
          height="120"
          rx="10"
          fill="rgba(255,255,255,0.05)"
          stroke="rgba(255,255,255,0.15)"
          strokeWidth={1}
        />
        <text x="450" y="325" textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize="14" fontFamily="'JetBrains Mono', monospace">
          CHASSIS
        </text>

        {/* Suspension arms */}
        {parts.map((part, i) => {
          const currentX = interpolate(explodeProgress, [0, 1], [part.x, part.x + part.explodeX]);
          const currentY = interpolate(explodeProgress, [0, 1], [part.y, part.y + part.explodeY]);

          // Airflow lines around each exploded part
          const showAirflow = explodeProgress > 0.5;

          return (
            <g key={i}>
              {/* Airflow arrows around exploded parts */}
              {showAirflow && (
                <>
                  {Array.from({ length: 3 }, (_, j) => {
                    const flowX = currentX + part.width * 0.3 + j * 20;
                    const flowY = currentY - 15 + j * 10;
                    const flowProgress = interpolate(
                      (frame + j * 10) % 60,
                      [0, 60],
                      [0, 60]
                    );
                    return (
                      <line
                        key={j}
                        x1={flowX}
                        y1={flowY}
                        x2={flowX + flowProgress * airflowReveal}
                        y2={flowY - 3}
                        stroke="#27F4D2"
                        strokeWidth={1}
                        opacity={airflowReveal * 0.5}
                      />
                    );
                  })}
                </>
              )}

              {/* The suspension arm */}
              <g transform={`translate(${currentX}, ${currentY}) rotate(${part.angle})`}>
                <rect
                  x={-part.width / 2}
                  y={-8}
                  width={part.width}
                  height={16}
                  rx={4}
                  fill={part.color}
                  opacity={0.8}
                />
                {/* Ball joints at ends */}
                <circle cx={-part.width / 2} cy={0} r={6} fill="white" opacity={0.5} />
                <circle cx={part.width / 2} cy={0} r={6} fill="white" opacity={0.5} />
              </g>

              {/* Label (shows when exploded) */}
              {explodeProgress > 0.7 && (
                <text
                  x={currentX}
                  y={currentY - 25}
                  textAnchor="middle"
                  fill="rgba(255,255,255,0.7)"
                  fontSize="13"
                  fontFamily="'JetBrains Mono', monospace"
                  opacity={interpolate(labelSpring, [0, 1], [0, 1])}
                >
                  {part.name}
                </text>
              )}
            </g>
          );
        })}

        {/* Dual-purpose labels */}
        {explodeProgress > 0.8 && (
          <>
            <g opacity={interpolate(labelSpring, [0, 1], [0, 1])}>
              {/* Structure label */}
              <rect x="100" y="180" width="180" height="50" rx="6" fill="rgba(206,220,0,0.1)" stroke="#CEDC00" strokeWidth={1} />
              <text x="190" y="200" textAnchor="middle" fill="#CEDC00" fontSize="12" fontFamily="'JetBrains Mono', monospace">STRUCTURAL</text>
              <text x="190" y="218" textAnchor="middle" fill="rgba(255,255,255,0.6)" fontSize="11" fontFamily="'Inter', sans-serif">Holds wheels, manages ride</text>

              {/* Aero label */}
              <rect x="100" y="380" width="180" height="50" rx="6" fill="rgba(0,111,98,0.1)" stroke="#006F62" strokeWidth={1} />
              <text x="190" y="400" textAnchor="middle" fill="#006F62" fontSize="12" fontFamily="'JetBrains Mono', monospace">AERODYNAMIC</text>
              <text x="190" y="418" textAnchor="middle" fill="rgba(255,255,255,0.6)" fontSize="11" fontFamily="'Inter', sans-serif">Shapes airflow, creates downforce</text>
            </g>
          </>
        )}
      </svg>

      {/* Bottom quote */}
      <div
        style={{
          position: "absolute",
          bottom: 140,
          left: 80,
          right: 80,
          padding: "16px 24px",
          background: "rgba(0,111,98,0.08)",
          borderLeft: "3px solid #006F62",
          borderRadius: "0 8px 8px 0",
          opacity: interpolate(phaseTime, [3, 4], [0, 1], {
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
            color: "rgba(255,255,255,0.7)",
          }}
        >
          "Like asking your garden fence to also be a solar panel. Except it works... we think."
        </div>
      </div>
    </AbsoluteFill>
  );
};
