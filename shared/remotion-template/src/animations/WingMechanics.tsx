import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// Alpine engineering deep dive: bookshelf in phone booth constraint
export const WingMechanics: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const phaseTime = frame / fps;
  const titleSpring = spring({ frame, fps, config: { damping: 14 }, durationInFrames: 25 });

  // Regulation box visualization
  const boxReveal = interpolate(phaseTime, [2, 4], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Endplate curve animation
  const endplateCurve = interpolate(phaseTime, [5, 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Airflow visualization
  const flowActive = phaseTime > 8;

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
          <div style={{ width: 8, height: 40, background: "#FF87BC", borderRadius: 4 }} />
          <div>
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 16,
                color: "#FF87BC",
                letterSpacing: 4,
              }}
            >
              ALPINE A526
            </div>
            <div
              style={{
                fontFamily: "'Orbitron', sans-serif",
                fontSize: 36,
                fontWeight: 700,
                color: "white",
              }}
            >
              ENGINEERING THE IMPOSSIBLE
            </div>
          </div>
        </div>
      </div>

      <svg width="900" height="450" viewBox="0 0 900 450" style={{ marginTop: 40 }}>
        {/* Regulation box constraint */}
        <rect
          x="250"
          y="100"
          width={boxReveal * 400}
          height={boxReveal * 250}
          fill="none"
          stroke="#E10600"
          strokeWidth={2}
          strokeDasharray="8,4"
          opacity={boxReveal * 0.6}
        />

        {/* "Tiny box" label */}
        {boxReveal > 0.8 && (
          <text
            x="450"
            y="90"
            textAnchor="middle"
            fill="#E10600"
            fontSize="14"
            fontFamily="'JetBrains Mono', monospace"
            opacity={boxReveal - 0.5}
          >
            FIA REGULATION BOX
          </text>
        )}

        {/* Rear wing inside the box */}
        <g transform="translate(450, 225)">
          {/* Main wing plane */}
          <path
            d="M -150 0 Q 0 -15, 150 0"
            fill="none"
            stroke="white"
            strokeWidth={3}
          />

          {/* Bottom-hinge flap (Alpine style) */}
          <g transform={`rotate(${interpolate(Math.sin(phaseTime * 0.8), [-1, 1], [0, 20])}, -150, 20)`}>
            <path
              d="M -150 20 Q 0 10, 150 20"
              fill="none"
              stroke="#FF87BC"
              strokeWidth={4}
            />
            <circle cx="-150" cy="20" r="4" fill="#FFD700" />
          </g>

          {/* Endplates curving outward */}
          <path
            d={`M -160 -40 Q ${-160 - endplateCurve * 15} -40, ${-160 - endplateCurve * 12} -20 L -160 60`}
            fill="none"
            stroke="#0093CC"
            strokeWidth={3}
            opacity={endplateCurve}
          />
          <path
            d={`M 160 -40 Q ${160 + endplateCurve * 15} -40, ${160 + endplateCurve * 12} -20 L 160 60`}
            fill="none"
            stroke="#0093CC"
            strokeWidth={3}
            opacity={endplateCurve}
          />

          {/* Curved endplate label */}
          {endplateCurve > 0.7 && (
            <>
              <line x1={-175} y1={-30} x2={-220} y2={-50} stroke="rgba(255,255,255,0.3)" strokeWidth={1} />
              <text x={-225} y={-55} textAnchor="end" fill="#0093CC" fontSize="12" fontFamily="'JetBrains Mono', monospace">
                Curved endplates
              </text>
              <text x={-225} y={-40} textAnchor="end" fill="rgba(255,255,255,0.4)" fontSize="11" fontFamily="'Inter', sans-serif">
                More airflow capacity
              </text>
            </>
          )}
        </g>

        {/* Airflow through curved endplates */}
        {flowActive && (
          <>
            {Array.from({ length: 6 }, (_, i) => {
              const speed = 1.5 + i * 0.3;
              const x = ((frame * speed + i * 40) % 500) + 200;
              const y = 180 + Math.sin(x / 50) * 20;
              return (
                <circle
                  key={i}
                  cx={x}
                  cy={y}
                  r={2}
                  fill="#27F4D2"
                  opacity={interpolate(phaseTime, [8, 9], [0, 0.5], {
                    extrapolateLeft: "clamp",
                    extrapolateRight: "clamp",
                  })}
                />
              );
            })}
          </>
        )}
      </svg>

      {/* Phone booth analogy */}
      <div
        style={{
          position: "absolute",
          bottom: 130,
          left: 80,
          right: 80,
          textAlign: "center",
          fontFamily: "'Inter', sans-serif",
          fontSize: 20,
          fontStyle: "italic",
          color: "rgba(255,255,255,0.6)",
          opacity: interpolate(phaseTime, [3, 4], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        "Imagine trying to build a bookshelf inside a phone booth"
      </div>

      {/* Respect callout */}
      <div
        style={{
          position: "absolute",
          bottom: 80,
          left: 0,
          right: 0,
          textAlign: "center",
          fontFamily: "'Inter', sans-serif",
          fontSize: 16,
          color: "rgba(255,255,255,0.4)",
          opacity: interpolate(phaseTime, [10, 11], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        "But what if we didn't?"
      </div>
    </AbsoluteFill>
  );
};
