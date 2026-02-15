import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// Red Bull: Sealed diffuser with only brake cooling outlets
export const DiffuserCutaway: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const phaseTime = frame / fps;
  const titleSpring = spring({ frame, fps, config: { damping: 14 }, durationInFrames: 25 });

  // Vacuum seal animation
  const sealProgress = interpolate(phaseTime, [3, 6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Air particles - only through brake ducts
  const particles = Array.from({ length: 15 }, (_, i) => {
    const speed = 1.2 + (i % 4) * 0.3;
    const x = ((frame * speed + i * 35) % 500) + 250;
    // Only particles near brake duct positions (y ~ 240 and y ~ 310) get through
    const brakeDuctY = i % 2 === 0 ? 240 : 310;
    const throughDuct = sealProgress > 0.5;
    const y = throughDuct ? brakeDuctY + Math.sin(x / 30) * 10 : 200 + i * 15;
    const blocked = !throughDuct && x > 400 && x < 600;
    return { x, y, opacity: blocked ? 0.1 : 0.5 };
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
          <div style={{ width: 8, height: 40, background: "#3671C6", borderRadius: 4 }} />
          <div>
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 16,
                color: "#3671C6",
                letterSpacing: 4,
              }}
            >
              RED BULL
            </div>
            <div
              style={{
                fontFamily: "'Orbitron', sans-serif",
                fontSize: 36,
                fontWeight: 700,
                color: "white",
              }}
            >
              VACUUM-SEALED DIFFUSER
            </div>
          </div>
        </div>
      </div>

      <svg width="900" height="400" viewBox="0 0 900 400" style={{ marginTop: 40 }}>
        {/* Car rear cross-section */}
        <path
          d="M 250 150 L 350 120 Q 450 110, 550 120 L 650 150 L 680 350 L 220 350 Z"
          fill="rgba(54,113,198,0.05)"
          stroke="rgba(255,255,255,0.2)"
          strokeWidth={1.5}
        />

        {/* Extremely tight bodywork */}
        <path
          d="M 300 160 Q 450 145, 600 160 L 620 180 Q 450 170, 280 180 Z"
          fill="rgba(54,113,198,0.1)"
          stroke="#3671C6"
          strokeWidth={2}
        />

        {/* "Sealed" panels - appear with sealProgress */}
        {sealProgress > 0 && (
          <>
            {/* Left seal */}
            <rect
              x="260"
              y="200"
              width={sealProgress * 80}
              height="120"
              fill="rgba(54,113,198,0.08)"
              stroke="#3671C6"
              strokeWidth={1}
              opacity={sealProgress}
            />
            {/* Right seal */}
            <rect
              x={640 - sealProgress * 80}
              y="200"
              width={sealProgress * 80}
              height="120"
              fill="rgba(54,113,198,0.08)"
              stroke="#3671C6"
              strokeWidth={1}
              opacity={sealProgress}
            />
            {/* X marks on sealed areas */}
            {sealProgress > 0.7 && (
              <>
                <text x="300" y="265" textAnchor="middle" fill="#E10600" fontSize="28" opacity={0.5}>
                  ✕
                </text>
                <text x="600" y="265" textAnchor="middle" fill="#E10600" fontSize="28" opacity={0.5}>
                  ✕
                </text>
              </>
            )}
          </>
        )}

        {/* Brake cooling outlets - the ONLY air entry */}
        <rect x="310" y="230" width="30" height="15" rx="3" fill="#FFD700" opacity={0.7} />
        <rect x="560" y="230" width="30" height="15" rx="3" fill="#FFD700" opacity={0.7} />

        {/* Labels for brake ducts */}
        {sealProgress > 0.8 && (
          <>
            <text x="325" y="222" textAnchor="middle" fill="#FFD700" fontSize="10" fontFamily="'JetBrains Mono', monospace">
              BRAKE DUCT
            </text>
            <text x="575" y="222" textAnchor="middle" fill="#FFD700" fontSize="10" fontFamily="'JetBrains Mono', monospace">
              BRAKE DUCT
            </text>
          </>
        )}

        {/* Diffuser at bottom */}
        <path
          d="M 280 340 Q 350 360, 450 370 Q 550 360, 620 340"
          fill="rgba(54,113,198,0.15)"
          stroke="#3671C6"
          strokeWidth={2}
        />
        <text x="450" y="365" textAnchor="middle" fill="#3671C6" fontSize="12" fontFamily="'JetBrains Mono', monospace">
          DIFFUSER
        </text>

        {/* Air particles */}
        {particles.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r={2.5} fill="#27F4D2" opacity={p.opacity} />
        ))}
      </svg>

      {/* Sealed vs Open comparison */}
      <div
        style={{
          position: "absolute",
          right: 80,
          top: 200,
          textAlign: "right",
          opacity: interpolate(phaseTime, [5, 6], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        <div style={{ marginBottom: 20 }}>
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 12,
              color: "rgba(255,255,255,0.4)",
              letterSpacing: 2,
            }}
          >
            OTHER TEAMS
          </div>
          <div
            style={{
              fontFamily: "'Inter', sans-serif",
              fontSize: 16,
              color: "rgba(255,255,255,0.5)",
            }}
          >
            Windows in a building
          </div>
        </div>
        <div>
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 12,
              color: "#3671C6",
              letterSpacing: 2,
            }}
          >
            RED BULL
          </div>
          <div
            style={{
              fontFamily: "'Inter', sans-serif",
              fontSize: 16,
              color: "#3671C6",
            }}
          >
            Sealed building + ventilation only
          </div>
        </div>
      </div>

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
          opacity: interpolate(phaseTime, [6, 7], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        "Zero wasted space. Every single surface has a purpose. Classic Red Bull."
      </div>
    </AbsoluteFill>
  );
};
