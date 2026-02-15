import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// Williams: Hidden suspension arms with progressive reveal
export const HiddenReveal: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const phaseTime = frame / fps;
  const titleSpring = spring({ frame, fps, config: { damping: 14 }, durationInFrames: 25 });

  // Cover panels that hide the suspension
  const coverOpacity = interpolate(phaseTime, [5, 9], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Hidden parts reveal
  const revealProgress = interpolate(phaseTime, [5, 9], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Sparkle effect on reveal
  const sparkles = Array.from({ length: 8 }, (_, i) => {
    const angle = (i / 8) * Math.PI * 2 + frame * 0.05;
    const dist = 80 + Math.sin(frame / 10 + i) * 20;
    return {
      x: 450 + Math.cos(angle) * dist,
      y: 280 + Math.sin(angle) * dist * 0.6,
      opacity: revealProgress > 0.5 ? interpolate(Math.sin(frame / 5 + i * 2), [-1, 1], [0.1, 0.5]) : 0,
    };
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
          <div style={{ width: 8, height: 40, background: "#64C4FF", borderRadius: 4 }} />
          <div>
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 16,
                color: "#64C4FF",
                letterSpacing: 4,
              }}
            >
              WILLIAMS FW48
            </div>
            <div
              style={{
                fontFamily: "'Orbitron', sans-serif",
                fontSize: 36,
                fontWeight: 700,
                color: "white",
              }}
            >
              HIDDEN IN PLAIN SIGHT
            </div>
          </div>
        </div>
      </div>

      <svg width="900" height="400" viewBox="0 0 900 400" style={{ marginTop: 30 }}>
        {/* Car silhouette */}
        <path
          d="M 250 250 L 320 220 Q 450 200, 580 220 L 650 250 L 650 310 L 250 310 Z"
          fill="rgba(100,196,255,0.05)"
          stroke="rgba(255,255,255,0.2)"
          strokeWidth={1.5}
        />

        {/* HIDDEN suspension arms (revealed progressively) */}
        {/* Front pullrod */}
        <g opacity={revealProgress}>
          <line x1="320" y1="240" x2="380" y2="290" stroke="#64C4FF" strokeWidth={3} />
          <circle cx="320" cy="240" r="4" fill="#FFD700" />
          <circle cx="380" cy="290" r="4" fill="#FFD700" />
          {revealProgress > 0.7 && (
            <text x="310" y="232" textAnchor="end" fill="#64C4FF" fontSize="11" fontFamily="'JetBrains Mono', monospace">
              PULLROD (front)
            </text>
          )}
        </g>

        {/* Front upper wishbone */}
        <g opacity={revealProgress}>
          <line x1="330" y1="230" x2="400" y2="260" stroke="#64C4FF" strokeWidth={2.5} />
          <line x1="330" y1="230" x2="370" y2="225" stroke="#64C4FF" strokeWidth={2.5} />
        </g>

        {/* Rear pushrod */}
        <g opacity={revealProgress}>
          <line x1="580" y1="240" x2="540" y2="210" stroke="#041E42" strokeWidth={3} />
          <circle cx="580" cy="240" r="4" fill="#FFD700" />
          <circle cx="540" cy="210" r="4" fill="#FFD700" />
          {revealProgress > 0.7 && (
            <text x="595" y="232" fill="#64C4FF" fontSize="11" fontFamily="'JetBrains Mono', monospace">
              PUSHROD (rear)
            </text>
          )}
        </g>

        {/* Rear wishbones */}
        <g opacity={revealProgress}>
          <line x1="570" y1="250" x2="510" y2="260" stroke="#041E42" strokeWidth={2.5} />
          <line x1="570" y1="250" x2="530" y2="245" stroke="#041E42" strokeWidth={2.5} />
        </g>

        {/* Cover panels (hide suspension) */}
        <rect
          x="300"
          y="215"
          width="120"
          height="85"
          rx="6"
          fill="rgba(100,100,100,0.3)"
          stroke="rgba(255,255,255,0.2)"
          strokeWidth={1}
          opacity={coverOpacity}
        />
        <rect
          x="520"
          y="215"
          width="100"
          height="85"
          rx="6"
          fill="rgba(100,100,100,0.3)"
          stroke="rgba(255,255,255,0.2)"
          strokeWidth={1}
          opacity={coverOpacity}
        />

        {/* "CLASSIFIED" stamps on covers */}
        {coverOpacity > 0.5 && (
          <>
            <text x="360" y="265" textAnchor="middle" fill="#E10600" fontSize="14"
              fontFamily="'Orbitron', sans-serif" fontWeight="700"
              transform="rotate(-10, 360, 265)" opacity={coverOpacity * 0.7}>
              CLASSIFIED
            </text>
            <text x="570" y="265" textAnchor="middle" fill="#E10600" fontSize="14"
              fontFamily="'Orbitron', sans-serif" fontWeight="700"
              transform="rotate(-10, 570, 265)" opacity={coverOpacity * 0.7}>
              CLASSIFIED
            </text>
          </>
        )}

        {/* Wheels */}
        <circle cx="310" cy="315" r="20" fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth={2} />
        <circle cx="590" cy="315" r="20" fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth={2} />

        {/* Sparkles on reveal */}
        {sparkles.map((s, i) => (
          <circle key={i} cx={s.x} cy={s.y} r={2} fill="#FFD700" opacity={s.opacity} />
        ))}

        {/* Split suspension label */}
        {revealProgress > 0.8 && (
          <g opacity={revealProgress - 0.5}>
            <text x="450" y="185" textAnchor="middle" fill="white" fontSize="16" fontFamily="'Orbitron', sans-serif" fontWeight="600">
              SPLIT SUSPENSION
            </text>
            <text x="450" y="200" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="12" fontFamily="'Inter', sans-serif">
              Only team on the grid with this approach
            </text>
          </g>
        )}
      </svg>

      {/* Quote */}
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
          opacity: interpolate(phaseTime, [8, 9], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        "Like watching your kid who struggled in school suddenly acing the test and refusing to let anyone see their notes"
      </div>
    </AbsoluteFill>
  );
};
