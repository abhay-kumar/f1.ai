import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// The hot take: wing mode transition is where championships are won
export const TransitionMoment: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const phaseTime = frame / fps;

  // Wing transition cycle: corner mode → straight mode
  const cycleProgress = (phaseTime % 6) / 6;
  const isCornerMode = cycleProgress < 0.5;
  const transitionSharpness = interpolate(
    Math.abs(cycleProgress - 0.5),
    [0, 0.05, 0.5],
    [0, 1, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // "Snap" effect during transition
  const snapIntensity = 1 - transitionSharpness;
  const titleSpring = spring({ frame, fps, config: { damping: 14 }, durationInFrames: 25 });

  // Force values
  const downforce = isCornerMode ? 100 : 30;
  const drag = isCornerMode ? 100 : 40;
  const speed = isCornerMode ? 65 : 100;

  // Colors
  const modeColor = isCornerMode ? "#27F4D2" : "#E10600";

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
          opacity: interpolate(titleSpring, [0, 1], [0, 1]),
        }}
      >
        <div
          style={{
            fontFamily: "'Orbitron', sans-serif",
            fontSize: 40,
            fontWeight: 700,
            color: "white",
          }}
        >
          THE TRANSITION MOMENT
        </div>
        <div
          style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: 20,
            color: "rgba(255,255,255,0.5)",
            marginTop: 8,
          }}
        >
          Where championships will be won and lost
        </div>
      </div>

      {/* Central car visualization */}
      <svg width="800" height="300" viewBox="0 0 800 300">
        {/* Car body */}
        <path
          d="M 200 160 L 280 140 Q 400 130, 520 140 L 600 160 L 600 200 L 200 200 Z"
          fill="rgba(255,255,255,0.08)"
          stroke={modeColor}
          strokeWidth={2}
          opacity={0.8}
        />

        {/* Front wing */}
        <g transform={`translate(220, 175)`}>
          <line
            x1="-30"
            y1="0"
            x2="30"
            y2={isCornerMode ? -15 : -3}
            stroke={modeColor}
            strokeWidth={4}
          />
        </g>

        {/* Rear wing - animated flap */}
        <g transform={`translate(580, 130)`}>
          {/* Main plane */}
          <line x1="-20" y1="10" x2="20" y2="10" stroke="white" strokeWidth={3} />
          {/* Moveable flap */}
          <line
            x1="-20"
            y1="0"
            x2="20"
            y2={isCornerMode ? -12 : 2}
            stroke={modeColor}
            strokeWidth={4}
          />
        </g>

        {/* Wheels */}
        <circle cx="260" cy="205" r="20" fill="none" stroke="rgba(255,255,255,0.3)" strokeWidth={2} />
        <circle cx="540" cy="205" r="20" fill="none" stroke="rgba(255,255,255,0.3)" strokeWidth={2} />

        {/* Downforce arrows */}
        {isCornerMode && (
          <>
            {[300, 400, 500].map((x, i) => (
              <g key={i} opacity={0.5}>
                <line x1={x} y1={100} x2={x} y2={125} stroke="#27F4D2" strokeWidth={2} />
                <polygon points={`${x - 4},125 ${x + 4},125 ${x},133`} fill="#27F4D2" />
              </g>
            ))}
          </>
        )}

        {/* Speed arrows (horizontal) */}
        {!isCornerMode && (
          <>
            {[150, 165, 180].map((y, i) => (
              <g key={i} opacity={0.5}>
                <line x1={620} y1={y} x2={680} y2={y} stroke="#E10600" strokeWidth={2} />
                <polygon points={`680,${y - 4} 680,${y + 4} 688,${y}`} fill="#E10600" />
              </g>
            ))}
          </>
        )}

        {/* Ground/track */}
        <line x1="100" y1="230" x2="700" y2="230" stroke="rgba(255,255,255,0.15)" strokeWidth={1} />
      </svg>

      {/* Snap flash during transition */}
      {snapIntensity > 0.5 && (
        <AbsoluteFill
          style={{
            background: `rgba(255, 255, 255, ${(snapIntensity - 0.5) * 0.15})`,
            pointerEvents: "none",
          }}
        />
      )}

      {/* Mode indicator */}
      <div
        style={{
          position: "absolute",
          top: 200,
          right: 100,
          textAlign: "right",
        }}
      >
        <div
          style={{
            fontFamily: "'Orbitron', sans-serif",
            fontSize: 28,
            fontWeight: 700,
            color: modeColor,
          }}
        >
          {isCornerMode ? "CORNER MODE" : "STRAIGHT MODE"}
        </div>
        <div
          style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: 16,
            color: "rgba(255,255,255,0.5)",
            marginTop: 4,
          }}
        >
          {isCornerMode ? "Max downforce, max grip" : "Min drag, max speed"}
        </div>
      </div>

      {/* Force gauges at bottom */}
      <div
        style={{
          position: "absolute",
          bottom: 180,
          left: 100,
          right: 100,
          display: "flex",
          justifyContent: "space-around",
        }}
      >
        {[
          { label: "DOWNFORCE", value: downforce, color: "#27F4D2" },
          { label: "DRAG", value: drag, color: "#E10600" },
          { label: "TOP SPEED", value: speed, color: "#FFD700" },
        ].map((gauge, i) => (
          <div key={i} style={{ width: 250 }}>
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 12,
                color: "rgba(255,255,255,0.4)",
                letterSpacing: 2,
                marginBottom: 8,
              }}
            >
              {gauge.label}
            </div>
            <div
              style={{
                width: "100%",
                height: 8,
                background: "rgba(255,255,255,0.08)",
                borderRadius: 4,
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${gauge.value}%`,
                  height: "100%",
                  background: gauge.color,
                  borderRadius: 4,
                  boxShadow: `0 0 10px ${gauge.color}44`,
                }}
              />
            </div>
            <div
              style={{
                fontFamily: "'Orbitron', sans-serif",
                fontSize: 20,
                color: gauge.color,
                marginTop: 4,
              }}
            >
              {gauge.value}%
            </div>
          </div>
        ))}
      </div>

      {/* Key insight callout */}
      <div
        style={{
          position: "absolute",
          bottom: 80,
          left: 0,
          right: 0,
          textAlign: "center",
          fontFamily: "'Inter', sans-serif",
          fontSize: 18,
          fontStyle: "italic",
          color: "rgba(255,255,255,0.5)",
          opacity: interpolate(phaseTime, [4, 5], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        "Get that transition butter-smooth, and you'll carry more speed everywhere."
      </div>
    </AbsoluteFill>
  );
};
