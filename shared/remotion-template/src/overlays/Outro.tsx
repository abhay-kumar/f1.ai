import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface OutroProps {
  duration: number;
  teamColor: string;
}

export const Outro: React.FC<OutroProps> = ({
  duration = 5,
  teamColor = "#E10600",
}) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const totalFrames = Math.ceil(duration * fps);
  const is4K = width >= 3840;
  const scale = is4K ? 2 : 1;

  // === Timing ===
  const logoStart = 0;
  const ctaStart = Math.ceil(fps * 0.4);
  const lineStart = Math.ceil(fps * 0.6);
  const fadeOutStart = totalFrames - Math.ceil(fps * 0.5);

  // === Background ===
  const bgOpacity = interpolate(frame, [0, 5], [0, 1], {
    extrapolateRight: "clamp",
  });

  // === Fade out ===
  const fadeOut = interpolate(frame, [fadeOutStart, totalFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // === Logo animation ===
  const logoSpring = spring({
    frame: frame - logoStart,
    fps,
    config: { damping: 14, stiffness: 100 },
  });
  const logoScale = interpolate(logoSpring, [0, 1], [0.6, 1]);
  const logoOpacity = interpolate(logoSpring, [0, 1], [0, 1]);
  // Logo already contains "F1 BURNOUTS" text — render large and crisp
  const logoWidth = is4K ? 700 : 400;
  const logoHeight = is4K ? 560 : 320;

  // === CTA items ===
  const ctaItems = [
    { icon: "👍", text: "LIKE" },
    { icon: "🔔", text: "SUBSCRIBE" },
    { icon: "💬", text: "COMMENT" },
  ];

  // === Accent lines ===
  const lineSpring = spring({
    frame: frame - lineStart,
    fps,
    config: { damping: 18, stiffness: 150 },
  });
  const lineW = is4K ? 700 : 420;
  const lineH = is4K ? 4 : 2;

  // === Subtle glow pulse on team color elements ===
  const glowPulse = interpolate(
    frame % Math.ceil(fps * 1.5),
    [0, Math.ceil(fps * 0.75), Math.ceil(fps * 1.5)],
    [0.5, 1, 0.5],
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: `rgba(11, 11, 11, ${bgOpacity})`,
        justifyContent: "center",
        alignItems: "center",
        opacity: fadeOut,
      }}
    >
      {/* Top accent line */}
      <div
        style={{
          position: "absolute",
          top: is4K ? "18%" : "18%",
          left: "50%",
          transform: `translateX(-50%) scaleX(${lineSpring})`,
          width: lineW,
          height: lineH,
          background: `linear-gradient(to right, transparent, ${teamColor}, transparent)`,
          boxShadow: `0 0 ${10 * scale}px ${teamColor}`,
          opacity: glowPulse,
        }}
      />

      {/* Logo — large, contains branding text already */}
      <div
        style={{
          position: "absolute",
          top: is4K ? "20%" : "20%",
          left: "50%",
          transform: `translateX(-50%) scale(${logoScale})`,
          opacity: logoOpacity,
        }}
      >
        <Img
          src={staticFile("logo.png")}
          style={{
            width: logoWidth,
            height: logoHeight,
            objectFit: "contain",
          }}
        />
      </div>

      {/* CTA items row */}
      <div
        style={{
          position: "absolute",
          top: is4K ? "62%" : "64%",
          left: "50%",
          transform: "translateX(-50%)",
          display: "flex",
          gap: is4K ? 120 : 70,
          alignItems: "center",
        }}
      >
        {ctaItems.map((item, i) => {
          const itemDelay = ctaStart + i * 4;
          const itemSpring = spring({
            frame: frame - itemDelay,
            fps,
            config: { damping: 12, stiffness: 120 },
          });
          const itemOpacity = interpolate(itemSpring, [0, 1], [0, 1]);
          const itemY = interpolate(itemSpring, [0, 1], [20 * scale, 0]);

          return (
            <div
              key={i}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: is4K ? 16 : 8,
                opacity: itemOpacity,
                transform: `translateY(${itemY}px)`,
              }}
            >
              <span style={{ fontSize: is4K ? 60 : 36 }}>{item.icon}</span>
              <span
                style={{
                  fontFamily: "'Formula1', 'Orbitron', sans-serif",
                  fontSize: is4K ? 30 : 18,
                  fontWeight: 700,
                  color: "white",
                  letterSpacing: is4K ? 4 : 2,
                }}
              >
                {item.text}
              </span>
            </div>
          );
        })}
      </div>

      {/* Bottom accent line */}
      <div
        style={{
          position: "absolute",
          bottom: is4K ? "18%" : "18%",
          left: "50%",
          transform: `translateX(-50%) scaleX(${lineSpring})`,
          width: lineW,
          height: lineH,
          background: `linear-gradient(to right, transparent, ${teamColor}, transparent)`,
          boxShadow: `0 0 ${10 * scale}px ${teamColor}`,
          opacity: glowPulse,
        }}
      />

      {/* "SEE YOU TOMORROW" at bottom */}
      <div
        style={{
          position: "absolute",
          bottom: is4K ? "12%" : "12%",
          left: "50%",
          transform: "translateX(-50%)",
          fontFamily: "'Formula1', 'Orbitron', sans-serif",
          fontSize: is4K ? 26 : 15,
          fontWeight: 700,
          color: "rgba(255,255,255,0.5)",
          letterSpacing: is4K ? 6 : 3,
          opacity: interpolate(frame, [ctaStart + 12, ctaStart + 20], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        SEE YOU TOMORROW
      </div>
    </AbsoluteFill>
  );
};
