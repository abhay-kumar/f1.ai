import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// Mercedes W17: Rising sidepods with underground tunnel visualization
export const SidepodComparison: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const phaseTime = frame / fps;
  const titleSpring = spring({ frame, fps, config: { damping: 14 }, durationInFrames: 25 });

  // Airflow animation through tunnel
  const flowSpeed = frame * 2;

  // Phase: conventional (0-8s) → flip to Mercedes (8s+)
  const showMercedes = phaseTime > 8;
  const mercedesEntrance = spring({
    frame: frame - 8 * fps,
    fps,
    config: { damping: 14 },
    durationInFrames: 30,
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
            color: "#27F4D2",
            letterSpacing: 4,
          }}
        >
          MERCEDES W17
        </div>
        <div
          style={{
            fontFamily: "'Orbitron', sans-serif",
            fontSize: 36,
            fontWeight: 700,
            color: "white",
          }}
        >
          {showMercedes ? "THE UPHILL WATERSLIDE" : "CONVENTIONAL APPROACH"}
        </div>
      </div>

      {/* Cross-section visualization */}
      <div style={{ display: "flex", gap: 60, alignItems: "center" }}>
        {/* Conventional sidepod - slopes down */}
        <div style={{ textAlign: "center", opacity: showMercedes ? 0.3 : 1 }}>
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 13,
              color: "rgba(255,255,255,0.5)",
              letterSpacing: 2,
              marginBottom: 16,
            }}
          >
            MOST TEAMS
          </div>
          <svg width="450" height="350" viewBox="0 0 450 350">
            {/* Car body outline */}
            <path
              d="M 50 200 L 100 180 Q 200 170, 300 200 L 400 220 L 400 280 L 50 280 Z"
              fill="rgba(255,255,255,0.05)"
              stroke="rgba(255,255,255,0.3)"
              strokeWidth={2}
            />

            {/* Sidepod top surface - slopes DOWN */}
            <path
              d="M 120 180 Q 220 170, 350 210"
              fill="none"
              stroke="#E10600"
              strokeWidth={3}
            />

            {/* Arrow showing downward slope */}
            <line x1="350" y1="215" x2="380" y2="225" stroke="#E10600" strokeWidth={2} opacity={0.6} />
            <polygon points="377,220 385,225 378,230" fill="#E10600" opacity={0.6} />

            {/* Airflow */}
            {Array.from({ length: 6 }, (_, i) => {
              const x = ((flowSpeed + i * 60) % 400) + 50;
              const y = interpolate(x, [50, 400], [165, 205], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              });
              return (
                <circle key={i} cx={x} cy={y} r={2.5} fill="#27F4D2" opacity={0.4} />
              );
            })}

            <text x="225" y="320" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="13" fontFamily="'Inter', sans-serif">
              Slopes down — gravity + airflow
            </text>
          </svg>
        </div>

        {/* VS */}
        <div
          style={{
            fontFamily: "'Orbitron', sans-serif",
            fontSize: 20,
            color: "rgba(255,255,255,0.3)",
          }}
        >
          VS
        </div>

        {/* Mercedes - rises at back with tunnel underneath */}
        <div style={{ textAlign: "center", opacity: showMercedes ? 1 : 0.5 }}>
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 13,
              color: "#27F4D2",
              letterSpacing: 2,
              marginBottom: 16,
            }}
          >
            MERCEDES W17
          </div>
          <svg width="450" height="350" viewBox="0 0 450 350">
            {/* Car body outline with raised sidepod */}
            <path
              d="M 50 200 L 100 190 Q 200 200, 300 170 L 400 160 L 400 280 L 50 280 Z"
              fill="rgba(255,255,255,0.05)"
              stroke="rgba(255,255,255,0.3)"
              strokeWidth={2}
            />

            {/* Sidepod top surface - rises UP */}
            <path
              d="M 120 190 Q 220 195, 350 165"
              fill="none"
              stroke="#27F4D2"
              strokeWidth={3}
            />

            {/* Arrow showing upward rise */}
            <line x1="350" y1="160" x2="380" y2="148" stroke="#27F4D2" strokeWidth={2} opacity={0.6} />
            <polygon points="377,143 385,148 378,153" fill="#27F4D2" opacity={0.6} />

            {/* THE TUNNEL underneath */}
            {showMercedes && (
              <g opacity={interpolate(mercedesEntrance, [0, 1], [0, 1])}>
                {/* Tunnel area highlighted */}
                <path
                  d="M 150 220 Q 250 230, 380 200 L 380 265 Q 250 270, 150 265 Z"
                  fill="rgba(39, 244, 210, 0.08)"
                  stroke="#27F4D2"
                  strokeWidth={1}
                  strokeDasharray="4,4"
                />

                {/* Tunnel airflow particles */}
                {Array.from({ length: 8 }, (_, i) => {
                  const x = ((flowSpeed * 1.5 + i * 40) % 250) + 150;
                  const y = interpolate(x, [150, 380], [240, 225], {
                    extrapolateLeft: "clamp",
                    extrapolateRight: "clamp",
                  });
                  return (
                    <circle key={i} cx={x} cy={y} r={2.5} fill="#27F4D2" opacity={0.7} />
                  );
                })}

                {/* Tunnel label */}
                <text x="260" y="250" textAnchor="middle" fill="#27F4D2" fontSize="11" fontFamily="'JetBrains Mono', monospace" opacity={0.8}>
                  TUNNEL
                </text>
              </g>
            )}

            <text x="225" y="320" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="13" fontFamily="'Inter', sans-serif">
              Rises up — creates tunnel below
            </text>
          </svg>
        </div>
      </div>

      {/* Shopping arcade analogy */}
      {showMercedes && (
        <div
          style={{
            position: "absolute",
            bottom: 140,
            left: 80,
            right: 80,
            textAlign: "center",
            opacity: interpolate(mercedesEntrance, [0, 1], [0, 1]),
          }}
        >
          <div
            style={{
              fontFamily: "'Inter', sans-serif",
              fontSize: 20,
              fontStyle: "italic",
              color: "rgba(255,255,255,0.6)",
            }}
          >
            "Think of it like a shopping arcade — open at both ends, covered on top"
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
