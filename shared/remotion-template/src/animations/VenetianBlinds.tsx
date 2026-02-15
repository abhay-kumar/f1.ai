import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// Animated explanation of active aero - wings opening/closing like Venetian blinds
export const VenetianBlinds: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Phase 1: Show the wing (0-3s)
  // Phase 2: Open blinds/flatten wing (3-6s)
  // Phase 3: Close blinds/corner mode (6-9s)
  // Phase 4: Cycle between modes (9s+)

  const phaseTime = frame / fps;
  const cyclePhase = phaseTime > 9 ? ((phaseTime - 9) % 4) / 4 : 0;

  // Wing flap angle: 0 = corner mode (angled for downforce), 1 = straight mode (flat)
  let flapOpenness: number;
  if (phaseTime < 3) {
    flapOpenness = 0; // Corner mode
  } else if (phaseTime < 6) {
    // Opening animation
    flapOpenness = interpolate(phaseTime, [3, 5.5], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  } else if (phaseTime < 9) {
    // Closing animation
    flapOpenness = interpolate(phaseTime, [6, 8.5], [1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  } else {
    // Continuous cycle
    flapOpenness = Math.sin(cyclePhase * Math.PI * 2) * 0.5 + 0.5;
  }

  // Airflow particles
  const particles = Array.from({ length: 25 }, (_, i) => {
    const baseSpeed = 2 + (i % 5) * 0.5;
    const speed = flapOpenness > 0.5 ? baseSpeed * 1.5 : baseSpeed;
    const x = ((frame * speed + i * 40) % 1300) - 100;
    const yBase = 300 + Math.sin(i * 1.7) * 150;
    // Particles deflect more in corner mode (downforce)
    const deflection = (1 - flapOpenness) * 80;
    const y = x > 500 && x < 900 ? yBase + deflection * ((x - 500) / 400) : yBase;
    const opacity = interpolate(x, [-100, 100, 1000, 1200], [0, 0.6, 0.6, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    return { x, y, opacity };
  });

  // Labels
  const labelEntrance = spring({ frame: frame - 30, fps, config: { damping: 15 } });

  // Drag/downforce indicators
  const dragValue = interpolate(flapOpenness, [0, 1], [100, 40]);
  const downforceValue = interpolate(flapOpenness, [0, 1], [100, 30]);

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      {/* Title */}
      <div
        style={{
          position: "absolute",
          top: 80,
          left: 80,
          fontFamily: "'Orbitron', sans-serif",
          fontSize: 36,
          fontWeight: 700,
          color: "white",
          opacity: interpolate(spring({ frame, fps, config: { damping: 15 } }), [0, 1], [0, 1]),
        }}
      >
        ACTIVE AERODYNAMICS
      </div>

      {/* Wing cross-section visualization */}
      <svg
        width="1000"
        height="500"
        viewBox="0 0 1000 500"
        style={{ marginTop: -40 }}
      >
        {/* Airflow particles */}
        {particles.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r={3}
            fill="#27F4D2"
            opacity={p.opacity}
          />
        ))}

        {/* Airflow lines */}
        {Array.from({ length: 8 }, (_, i) => {
          const yBase = 200 + i * 40;
          const deflect = (1 - flapOpenness) * (60 + i * 10);
          return (
            <path
              key={`flow-${i}`}
              d={`M 100 ${yBase} C 400 ${yBase}, 600 ${yBase + deflect * 0.3}, 900 ${yBase + deflect}`}
              fill="none"
              stroke="#27F4D2"
              strokeWidth={1.5}
              opacity={0.15}
            />
          );
        })}

        {/* Wing main plane (static) */}
        <path
          d="M 350 280 Q 500 260, 700 275"
          fill="none"
          stroke="white"
          strokeWidth={4}
          strokeLinecap="round"
        />

        {/* Wing flap (moveable - the Venetian blind) */}
        {[0, 1, 2].map((flapIdx) => {
          const flapAngle = interpolate(flapOpenness, [0, 1], [25, 0]);
          const flapX = 480 + flapIdx * 80;
          const flapY = 270 + flapIdx * 3;
          return (
            <g
              key={`flap-${flapIdx}`}
              transform={`translate(${flapX}, ${flapY}) rotate(${-flapAngle})`}
            >
              <rect
                x={-35}
                y={-4}
                width={70}
                height={8}
                rx={3}
                fill={flapOpenness > 0.5 ? "#E10600" : "#27F4D2"}
                opacity={0.9}
              />
              {/* Hinge point */}
              <circle cx={-35} cy={0} r={4} fill="white" opacity={0.5} />
            </g>
          );
        })}

        {/* Downforce arrows */}
        {(1 - flapOpenness) > 0.3 && (
          <>
            <line
              x1="550"
              y1="310"
              x2="550"
              y2={310 + (1 - flapOpenness) * 80}
              stroke="#E10600"
              strokeWidth={3}
              opacity={1 - flapOpenness}
            />
            <polygon
              points={`545,${310 + (1 - flapOpenness) * 80} 555,${310 + (1 - flapOpenness) * 80} 550,${310 + (1 - flapOpenness) * 80 + 10}`}
              fill="#E10600"
              opacity={1 - flapOpenness}
            />
          </>
        )}
      </svg>

      {/* Mode label */}
      <div
        style={{
          position: "absolute",
          top: 140,
          right: 80,
          textAlign: "right",
          opacity: interpolate(labelEntrance, [0, 1], [0, 1]),
        }}
      >
        <div
          style={{
            fontFamily: "'Orbitron', sans-serif",
            fontSize: 24,
            fontWeight: 700,
            color: flapOpenness > 0.5 ? "#E10600" : "#27F4D2",
            transition: "color 0.3s",
          }}
        >
          {flapOpenness > 0.5 ? "STRAIGHT MODE" : "CORNER MODE"}
        </div>
        <div
          style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: 16,
            color: "rgba(255,255,255,0.5)",
            marginTop: 4,
          }}
        >
          {flapOpenness > 0.5
            ? "Wings flattened — low drag, high speed"
            : "Wings angled — maximum downforce"}
        </div>
      </div>

      {/* Stats panel */}
      <div
        style={{
          position: "absolute",
          bottom: 180,
          left: 80,
          display: "flex",
          gap: 60,
          opacity: interpolate(labelEntrance, [0, 1], [0, 1]),
        }}
      >
        {/* Drag meter */}
        <div>
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 14,
              color: "rgba(255,255,255,0.5)",
              letterSpacing: 2,
              marginBottom: 8,
            }}
          >
            DRAG
          </div>
          <div style={{ width: 200, height: 6, background: "rgba(255,255,255,0.1)", borderRadius: 3 }}>
            <div
              style={{
                width: `${dragValue}%`,
                height: "100%",
                background: "#E10600",
                borderRadius: 3,
              }}
            />
          </div>
          <div
            style={{
              fontFamily: "'Orbitron', sans-serif",
              fontSize: 20,
              color: "#E10600",
              marginTop: 6,
            }}
          >
            {Math.round(dragValue)}%
          </div>
        </div>

        {/* Downforce meter */}
        <div>
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 14,
              color: "rgba(255,255,255,0.5)",
              letterSpacing: 2,
              marginBottom: 8,
            }}
          >
            DOWNFORCE
          </div>
          <div style={{ width: 200, height: 6, background: "rgba(255,255,255,0.1)", borderRadius: 3 }}>
            <div
              style={{
                width: `${downforceValue}%`,
                height: "100%",
                background: "#27F4D2",
                borderRadius: 3,
              }}
            />
          </div>
          <div
            style={{
              fontFamily: "'Orbitron', sans-serif",
              fontSize: 20,
              color: "#27F4D2",
              marginTop: 6,
            }}
          >
            {Math.round(downforceValue)}%
          </div>
        </div>
      </div>

      {/* Venetian blind analogy callout */}
      {phaseTime > 2 && phaseTime < 7 && (
        <div
          style={{
            position: "absolute",
            bottom: 180,
            right: 80,
            padding: "16px 24px",
            background: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: 8,
            fontFamily: "'Inter', sans-serif",
            fontSize: 18,
            color: "rgba(255,255,255,0.7)",
            fontStyle: "italic",
            maxWidth: 350,
            opacity: interpolate(
              phaseTime,
              [2, 2.5, 6.5, 7],
              [0, 1, 1, 0],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
            ),
          }}
        >
          "Imagine opening a Venetian blind"
        </div>
      )}
    </AbsoluteFill>
  );
};
