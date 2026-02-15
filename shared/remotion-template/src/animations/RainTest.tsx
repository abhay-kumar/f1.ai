import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  random,
} from "remotion";

// Ferrari: Testing active aero in the rain at Barcelona
export const RainTest: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const phaseTime = frame / fps;
  const titleSpring = spring({ frame, fps, config: { damping: 14 }, durationInFrames: 25 });

  // Rain intensity builds
  const rainIntensity = interpolate(phaseTime, [2, 5], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Rain drops
  const rainDrops = Array.from({ length: 60 }, (_, i) => {
    const x = random(`rain-x-${i}`) * 1920;
    const speed = 8 + random(`rain-speed-${i}`) * 6;
    const y = ((frame * speed + random(`rain-offset-${i}`) * 1080) % 1200) - 100;
    const length = 15 + random(`rain-len-${i}`) * 15;
    return { x, y, length };
  });

  // Active aero flap cycling in wet conditions
  const wetFlapAngle = interpolate(
    Math.sin(phaseTime * 1.5),
    [-1, 1],
    [5, 25]
  );

  // Water spray from wheels
  const sprayActive = rainIntensity > 0.5;

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      {/* Title */}
      <div
        style={{
          position: "absolute",
          top: 80,
          left: 80,
          opacity: interpolate(titleSpring, [0, 1], [0, 1]),
          zIndex: 10,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ width: 8, height: 40, background: "#E8002D", borderRadius: 4 }} />
          <div>
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 16,
                color: "#E8002D",
                letterSpacing: 4,
              }}
            >
              FERRARI
            </div>
            <div
              style={{
                fontFamily: "'Orbitron', sans-serif",
                fontSize: 36,
                fontWeight: 700,
                color: "white",
              }}
            >
              WET-WEATHER GAMBIT
            </div>
          </div>
        </div>
      </div>

      {/* Rain overlay */}
      <AbsoluteFill style={{ opacity: rainIntensity * 0.7 }}>
        <svg width="1920" height="1080">
          {rainDrops.map((drop, i) => (
            <line
              key={i}
              x1={drop.x}
              y1={drop.y}
              x2={drop.x - 2}
              y2={drop.y + drop.length}
              stroke="rgba(150,180,255,0.3)"
              strokeWidth={1}
            />
          ))}
        </svg>
      </AbsoluteFill>

      {/* Car with active aero in rain */}
      <svg width="800" height="350" viewBox="0 0 800 350" style={{ marginTop: 20 }}>
        {/* Wet track */}
        <rect x="50" y="285" width="700" height="30" rx="3" fill="rgba(150,180,255,0.05)" />
        <line x1="50" y1="285" x2="750" y2="285" stroke="rgba(150,180,255,0.2)" strokeWidth={1} />

        {/* Car body */}
        <path
          d="M 200 210 L 280 190 Q 400 180, 520 190 L 600 210 L 600 260 L 200 260 Z"
          fill="rgba(232,0,45,0.12)"
          stroke="#E8002D"
          strokeWidth={2}
        />

        {/* Front wing with active aero */}
        <g transform={`translate(220, 240)`}>
          <line x1="-40" y1="0" x2="40" y2="0" stroke="white" strokeWidth={3} />
          <g transform={`rotate(${-wetFlapAngle}, -30, -5)`}>
            <line x1="-30" y1="-5" x2="30" y2="-5" stroke="#FFF200" strokeWidth={3} />
          </g>
        </g>

        {/* Rear wing with active aero */}
        <g transform={`translate(580, 175)`}>
          <line x1="-25" y1="15" x2="25" y2="15" stroke="white" strokeWidth={3} />
          <g transform={`rotate(${-wetFlapAngle}, -20, 0)`}>
            <line x1="-20" y1="0" x2="20" y2="0" stroke="#FFF200" strokeWidth={3} />
          </g>
        </g>

        {/* Wheels */}
        <circle cx="260" cy="265" r="22" fill="none" stroke="rgba(255,255,255,0.3)" strokeWidth={2} />
        <circle cx="540" cy="265" r="22" fill="none" stroke="rgba(255,255,255,0.3)" strokeWidth={2} />

        {/* Water spray from wheels */}
        {sprayActive && (
          <>
            {Array.from({ length: 8 }, (_, i) => {
              const angle = -30 + i * 10 + Math.sin(frame / 3 + i) * 5;
              const dist = 25 + Math.sin(frame / 5 + i * 2) * 10;
              return (
                <g key={i}>
                  <circle
                    cx={260 - Math.cos((angle * Math.PI) / 180) * dist}
                    cy={265 - Math.sin((angle * Math.PI) / 180) * dist}
                    r={2}
                    fill="rgba(150,180,255,0.4)"
                  />
                  <circle
                    cx={540 - Math.cos((angle * Math.PI) / 180) * dist}
                    cy={265 - Math.sin((angle * Math.PI) / 180) * dist}
                    r={2}
                    fill="rgba(150,180,255,0.4)"
                  />
                </g>
              );
            })}
          </>
        )}

        {/* Rain hitting wing surfaces */}
        {rainIntensity > 0.3 && (
          <>
            {Array.from({ length: 5 }, (_, i) => {
              const splashX = 350 + i * 50 + Math.sin(frame / 4 + i) * 10;
              const splashY = 180 + Math.cos(i * 1.5) * 15;
              return (
                <circle
                  key={i}
                  cx={splashX}
                  cy={splashY}
                  r={1.5 + Math.sin(frame / 3 + i) * 0.5}
                  fill="rgba(150,180,255,0.5)"
                />
              );
            })}
          </>
        )}
      </svg>

      {/* Data advantage callout */}
      <div
        style={{
          position: "absolute",
          right: 80,
          top: 200,
          padding: "20px 24px",
          background: "rgba(232,0,45,0.08)",
          border: "1px solid rgba(232,0,45,0.3)",
          borderRadius: 8,
          maxWidth: 300,
          opacity: interpolate(phaseTime, [5, 6], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 12,
            color: "#FFF200",
            letterSpacing: 2,
            marginBottom: 8,
          }}
        >
          DATA ADVANTAGE
        </div>
        <div
          style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: 16,
            color: "rgba(255,255,255,0.7)",
            lineHeight: 1.4,
          }}
        >
          Only team to test active aero in wet conditions. Others have zero rain data.
        </div>
      </div>

      {/* Pushrod return note */}
      <div
        style={{
          position: "absolute",
          bottom: 180,
          right: 80,
          padding: "16px 20px",
          background: "rgba(255,255,255,0.03)",
          borderLeft: "3px solid #E8002D",
          borderRadius: "0 6px 6px 0",
          opacity: interpolate(phaseTime, [8, 9], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 12,
            color: "#E8002D",
            letterSpacing: 2,
          }}
        >
          PUSHROD RETURN
        </div>
        <div
          style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: 14,
            color: "rgba(255,255,255,0.5)",
            marginTop: 4,
          }}
        >
          First since 2011 — 15-year reversal
        </div>
      </div>

      {/* Bottom quote */}
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
        "Sometimes doing something mad. Sometimes doing something genius. Often both at the same time."
      </div>
    </AbsoluteFill>
  );
};
