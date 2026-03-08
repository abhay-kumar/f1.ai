import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface LowerThirdProps {
  title: string;
  teamColor: string;
  duration: number;
}

export const LowerThird: React.FC<LowerThirdProps> = ({
  title = "STORY TITLE",
  teamColor = "#E10600",
  duration = 3.5,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const totalFrames = Math.ceil(duration * fps);
  const is4K = width >= 3840;
  const scale = is4K ? 2 : 1;

  // Timing (in frames)
  const enterStart = 0;
  const enterEnd = Math.ceil(fps * 0.5); // 0.5s entrance
  const exitStart = totalFrames - Math.ceil(fps * 0.6); // 0.6s exit
  const exitEnd = totalFrames;

  // Entrance springs (staggered)
  const accentSpring = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 120 },
    durationInFrames: enterEnd,
  });

  const panelSpring = spring({
    frame: frame - 3,
    fps,
    config: { damping: 16, stiffness: 100 },
    durationInFrames: enterEnd,
  });

  const titleSpring = spring({
    frame: frame - 6,
    fps,
    config: { damping: 14, stiffness: 110 },
    durationInFrames: enterEnd,
  });

  const brandSpring = spring({
    frame: frame - 9,
    fps,
    config: { damping: 16, stiffness: 100 },
    durationInFrames: enterEnd,
  });

  const glowSpring = spring({
    frame: frame - 12,
    fps,
    config: { damping: 20, stiffness: 80 },
    durationInFrames: enterEnd,
  });

  // Exit animation
  const exitProgress = interpolate(frame, [exitStart, exitEnd], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const exitSlide = interpolate(exitProgress, [0, 1], [0, -40 * scale]);
  const exitOpacity = interpolate(exitProgress, [0, 0.7, 1], [1, 0.5, 0]);

  // Dimensions
  const accentW = 6 * scale;
  const panelW = 550 * scale;
  const panelH = 90 * scale;
  const bottomOffset = 40 * scale;
  const leftOffset = 20 * scale;
  const titleSize = is4K ? 44 : 28;
  const brandSize = is4K ? 26 : 16;
  const textLeft = leftOffset + accentW + 10 * scale;

  // Panel position from bottom
  const panelY = height - panelH - bottomOffset;

  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          left: leftOffset,
          top: panelY,
          width: panelW,
          height: panelH,
          transform: `translateX(${exitSlide}px)`,
          opacity: exitOpacity,
        }}
      >
        {/* Dark gradient panel - expands from left */}
        <div
          style={{
            position: "absolute",
            left: accentW,
            top: 0,
            width: interpolate(panelSpring, [0, 1], [0, panelW - accentW]),
            height: panelH,
            background:
              "linear-gradient(to right, rgba(0,0,0,0.8) 80%, rgba(0,0,0,0.0))",
            borderRadius: `0 ${4 * scale}px ${4 * scale}px 0`,
            overflow: "hidden",
          }}
        />

        {/* Team accent bar - slides in vertically */}
        <div
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            width: accentW,
            height: panelH,
            backgroundColor: teamColor,
            transform: `scaleY(${accentSpring})`,
            transformOrigin: "bottom",
            borderRadius: `${2 * scale}px 0 0 ${2 * scale}px`,
          }}
        />

        {/* Glow line under panel */}
        <div
          style={{
            position: "absolute",
            left: accentW,
            bottom: -2 * scale,
            width: interpolate(
              glowSpring,
              [0, 1],
              [0, (panelW - accentW) * 0.6]
            ),
            height: 1 * scale,
            background: `linear-gradient(to right, ${teamColor}, transparent)`,
            opacity: interpolate(glowSpring, [0, 1], [0, 0.7]),
            boxShadow: `0 0 ${8 * scale}px ${teamColor}`,
          }}
        />

        {/* Title text */}
        <div
          style={{
            position: "absolute",
            left: textLeft - leftOffset,
            top: 12 * scale,
            fontFamily: "'Formula1', 'Orbitron', sans-serif",
            fontSize: titleSize,
            fontWeight: 700,
            color: "white",
            letterSpacing: 1 * scale,
            whiteSpace: "nowrap",
            opacity: interpolate(titleSpring, [0, 1], [0, 1]),
            transform: `translateX(${interpolate(titleSpring, [0, 1], [-20 * scale, 0])}px)`,
          }}
        >
          {title}
        </div>

        {/* F1 BURNOUTS branding */}
        <div
          style={{
            position: "absolute",
            left: textLeft - leftOffset,
            bottom: 12 * scale,
            fontFamily: "'Formula1', 'Orbitron', sans-serif",
            fontSize: brandSize,
            fontWeight: 700,
            color: teamColor,
            letterSpacing: 2 * scale,
            whiteSpace: "nowrap",
            opacity: interpolate(brandSpring, [0, 1], [0, 0.9]),
          }}
        >
          F1 BURNOUTS
        </div>
      </div>
    </AbsoluteFill>
  );
};
