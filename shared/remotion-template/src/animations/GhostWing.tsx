import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// Alpine's inverted rear wing: bottom hinge, trailing edge drops down
export const GhostWing: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const phaseTime = frame / fps;

  // Show conventional wing first, then Alpine's ghost wing
  const showConventional = phaseTime < 12;

  // Conventional: flap lifts from front (letterbox)
  const conventionalOpen = showConventional
    ? interpolate(
        Math.sin((phaseTime - 3) * 0.8),
        [-1, 1],
        [0, 1],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
      )
    : 0;

  // Ghost wing: trailing edge drops from bottom hinge
  const ghostOpen = !showConventional
    ? interpolate(
        Math.sin((phaseTime - 14) * 0.8),
        [-1, 1],
        [0, 1],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
      )
    : 0;

  // Transition flash
  const transitionFlash = interpolate(phaseTime, [11, 12, 13], [0, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // "VS" label
  const titleEntrance = spring({ frame, fps, config: { damping: 14 }, durationInFrames: 25 });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      {/* Title */}
      <div
        style={{
          position: "absolute",
          top: 80,
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: interpolate(titleEntrance, [0, 1], [0, 1]),
        }}
      >
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
            fontSize: 40,
            fontWeight: 700,
            color: "white",
          }}
        >
          THE GHOST WING
        </div>
      </div>

      {/* Side-by-side comparison */}
      <div
        style={{
          display: "flex",
          gap: 80,
          alignItems: "center",
          marginTop: 20,
        }}
      >
        {/* Conventional wing */}
        <div style={{ textAlign: "center", opacity: showConventional ? 1 : 0.3 }}>
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 14,
              color: "rgba(255,255,255,0.5)",
              letterSpacing: 2,
              marginBottom: 20,
            }}
          >
            CONVENTIONAL (9 TEAMS)
          </div>
          <svg width="400" height="300" viewBox="0 0 400 300">
            {/* Endplates */}
            <rect x="50" y="80" width="8" height="160" rx="3" fill="rgba(255,255,255,0.2)" />
            <rect x="342" y="80" width="8" height="160" rx="3" fill="rgba(255,255,255,0.2)" />

            {/* Main wing plane (static) */}
            <path
              d="M 70 180 Q 200 165, 340 180"
              fill="none"
              stroke="white"
              strokeWidth={4}
            />

            {/* Moveable flap - lifts from front (letterbox) */}
            <g transform={`translate(200, 150) rotate(${-conventionalOpen * 25})`}>
              <path
                d="M -130 0 Q 0 -10, 130 0"
                fill="none"
                stroke="#3671C6"
                strokeWidth={6}
              />
              {/* Hinge point at leading edge */}
              <circle cx="-130" cy="0" r="5" fill="#FFD700" />
            </g>

            {/* Airflow arrows */}
            {conventionalOpen > 0.3 && (
              <>
                {Array.from({ length: 5 }, (_, i) => {
                  const x = 100 + i * 50;
                  const gap = conventionalOpen * 20;
                  return (
                    <g key={i} opacity={conventionalOpen * 0.6}>
                      <line x1={x} y1={130 - gap} x2={x} y2={130 + gap} stroke="#27F4D2" strokeWidth={1.5} />
                      <polygon points={`${x - 4},${130 + gap} ${x + 4},${130 + gap} ${x},${130 + gap + 8}`} fill="#27F4D2" />
                    </g>
                  );
                })}
              </>
            )}

            {/* Label */}
            <text x="200" y="270" textAnchor="middle" fill="rgba(255,255,255,0.5)" fontSize="13" fontFamily="'Inter', sans-serif">
              Front lifts up → air passes through
            </text>
          </svg>
        </div>

        {/* VS divider */}
        <div
          style={{
            fontFamily: "'Orbitron', sans-serif",
            fontSize: 24,
            color: "rgba(255,255,255,0.3)",
            opacity: interpolate(transitionFlash, [0, 1], [0.3, 1]),
          }}
        >
          VS
        </div>

        {/* Ghost wing (Alpine) */}
        <div style={{ textAlign: "center", opacity: !showConventional ? 1 : 0.3 }}>
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 14,
              color: "#FF87BC",
              letterSpacing: 2,
              marginBottom: 20,
            }}
          >
            ALPINE "GHOST WING"
          </div>
          <svg width="400" height="300" viewBox="0 0 400 300">
            {/* Endplates - curved outward at top */}
            <path d="M 58 80 Q 45 80, 50 100 L 50 240" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth={8} />
            <path d="M 342 80 Q 355 80, 350 100 L 350 240" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth={8} />

            {/* Main wing plane (static - stays on top) */}
            <path
              d="M 70 140 Q 200 125, 340 140"
              fill="none"
              stroke="white"
              strokeWidth={4}
            />

            {/* Moveable flap - hinged at BOTTOM, trailing edge drops */}
            <g transform={`translate(200, 170)`}>
              <g transform={`rotate(${ghostOpen * 30}, -130, 0)`}>
                <path
                  d="M -130 0 Q 0 -8, 130 0"
                  fill="none"
                  stroke="#FF87BC"
                  strokeWidth={6}
                />
                {/* Hinge at bottom/leading edge */}
                <circle cx="-130" cy="0" r="5" fill="#FFD700" />
              </g>
            </g>

            {/* Air flows OVER the top when ghost activates */}
            {ghostOpen > 0.3 && (
              <>
                {Array.from({ length: 5 }, (_, i) => {
                  const startX = 80 + i * 55;
                  const offset = ghostOpen * 30;
                  return (
                    <path
                      key={i}
                      d={`M ${startX} ${120 - offset * 0.3} Q ${startX + 30} ${120}, ${startX + 60} ${120 + offset * 0.5}`}
                      fill="none"
                      stroke="#27F4D2"
                      strokeWidth={1.5}
                      opacity={ghostOpen * 0.6}
                    />
                  );
                })}
              </>
            )}

            {/* Label */}
            <text x="200" y="270" textAnchor="middle" fill="rgba(255,255,255,0.5)" fontSize="13" fontFamily="'Inter', sans-serif">
              Bottom drops down → top stays still
            </text>
          </svg>
        </div>
      </div>

      {/* Transition flash overlay */}
      <AbsoluteFill
        style={{
          background: `rgba(255, 135, 188, ${transitionFlash * 0.1})`,
          pointerEvents: "none",
        }}
      />

      {/* Ghost wing explanation */}
      {!showConventional && (
        <div
          style={{
            position: "absolute",
            bottom: 140,
            left: 80,
            right: 80,
            textAlign: "center",
            opacity: interpolate(phaseTime, [13, 14], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          <div
            style={{
              fontFamily: "'Inter', sans-serif",
              fontSize: 20,
              color: "rgba(255,255,255,0.6)",
              fontStyle: "italic",
            }}
          >
            "It moves in a way that just looks... wrong"
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
