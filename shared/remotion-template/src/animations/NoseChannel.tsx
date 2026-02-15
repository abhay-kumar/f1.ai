import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// Mercedes/AM: Secret nose channel - hidden passage in a castle
export const NoseChannel: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const phaseTime = frame / fps;
  const titleSpring = spring({ frame, fps, config: { damping: 14 }, durationInFrames: 25 });

  // Reveal the hidden channel
  const channelReveal = interpolate(phaseTime, [4, 7], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Airflow through channel
  const flowParticles = Array.from({ length: 10 }, (_, i) => {
    const speed = 2 + i * 0.3;
    const progress = ((frame * speed + i * 30) % 300) / 300;
    const x = interpolate(progress, [0, 1], [250, 500]);
    const y = interpolate(progress, [0, 0.3, 0.7, 1], [240, 235, 232, 230]);
    return { x, y, opacity: channelReveal * 0.6 };
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
          <div style={{ width: 8, height: 40, background: "#27F4D2", borderRadius: 4 }} />
          <div>
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 16,
                color: "#27F4D2",
                letterSpacing: 4,
              }}
            >
              MERCEDES + ASTON MARTIN
            </div>
            <div
              style={{
                fontFamily: "'Orbitron', sans-serif",
                fontSize: 36,
                fontWeight: 700,
                color: "white",
              }}
            >
              THE HIDDEN CHANNEL
            </div>
          </div>
        </div>
      </div>

      <svg width="900" height="400" viewBox="0 0 900 400" style={{ marginTop: 30 }}>
        {/* Front wing - main plane */}
        <path
          d="M 150 260 Q 350 240, 550 260"
          fill="none"
          stroke="white"
          strokeWidth={3}
        />

        {/* Front wing - second element */}
        <path
          d="M 180 245 Q 350 225, 520 245"
          fill="none"
          stroke="rgba(255,255,255,0.5)"
          strokeWidth={2}
        />

        {/* Nose cone */}
        <path
          d="M 320 180 L 380 180 L 400 230 Q 350 225, 300 230 Z"
          fill="rgba(39,244,210,0.08)"
          stroke="rgba(255,255,255,0.3)"
          strokeWidth={2}
        />

        {/* Nose attachment point - to SECOND element (unique) */}
        <line x1="350" y1="220" x2="350" y2="240" stroke="#27F4D2" strokeWidth={3} />
        <circle cx="350" cy="240" r="5" fill="#27F4D2" />

        {/* Normal attachment point (ghosted) */}
        <line x1="350" y1="250" x2="350" y2="260" stroke="rgba(255,255,255,0.15)" strokeWidth={2} strokeDasharray="3,3" />

        {/* Labels */}
        <text x="380" y="252" fill="#27F4D2" fontSize="12" fontFamily="'JetBrains Mono', monospace">
          2nd element ✓
        </text>
        <text x="380" y="272" fill="rgba(255,255,255,0.3)" fontSize="12" fontFamily="'JetBrains Mono', monospace">
          Main plane (others)
        </text>

        {/* THE SECRET CHANNEL underneath nose */}
        <path
          d={`M 300 235 Q 350 ${235 - channelReveal * 8}, 400 235`}
          fill="none"
          stroke="#FFD700"
          strokeWidth={2}
          opacity={channelReveal}
          strokeDasharray={channelReveal > 0.8 ? "none" : "4,4"}
        />

        {/* Channel highlight area */}
        {channelReveal > 0.3 && (
          <path
            d="M 300 232 Q 350 224, 400 232 L 400 240 Q 350 238, 300 240 Z"
            fill="rgba(255,215,0,0.1)"
            stroke="none"
            opacity={channelReveal}
          />
        )}

        {/* Channel label */}
        {channelReveal > 0.5 && (
          <>
            <line x1="350" y1="224" x2="350" y2="180" stroke="rgba(255,215,0,0.3)" strokeWidth={1} />
            <text x="350" y="170" textAnchor="middle" fill="#FFD700" fontSize="13" fontFamily="'JetBrains Mono', monospace" opacity={channelReveal}>
              SECRET CHANNEL
            </text>
          </>
        )}

        {/* Airflow through channel */}
        {flowParticles.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r={2} fill="#FFD700" opacity={p.opacity} />
        ))}

        {/* Trade-off panel */}
        {channelReveal > 0.7 && (
          <g opacity={channelReveal - 0.3}>
            <rect x="600" y="160" width="240" height="120" rx="8" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.1)" strokeWidth={1} />
            <text x="620" y="185" fill="rgba(255,255,255,0.5)" fontSize="12" fontFamily="'JetBrains Mono', monospace">TRADE-OFF</text>
            <text x="620" y="210" fill="#E10600" fontSize="13" fontFamily="'Inter', sans-serif">✕ Less wing transformation</text>
            <text x="620" y="232" fill="#27F4D2" fontSize="13" fontFamily="'Inter', sans-serif">✓ Shorter, cleaner nose</text>
            <text x="620" y="254" fill="#FFD700" fontSize="13" fontFamily="'Inter', sans-serif">✓ Secret air channel</text>
          </g>
        )}
      </svg>

      {/* Castle analogy */}
      <div
        style={{
          position: "absolute",
          bottom: 120,
          left: 80,
          right: 80,
          textAlign: "center",
          fontFamily: "'Inter', sans-serif",
          fontSize: 20,
          fontStyle: "italic",
          color: "rgba(255,255,255,0.6)",
          opacity: interpolate(phaseTime, [7, 8], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        "The F1 equivalent of a hidden passage in a castle. Nobody sees it, but it changes everything."
      </div>
    </AbsoluteFill>
  );
};
