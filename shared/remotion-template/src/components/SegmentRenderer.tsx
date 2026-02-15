import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { Segment, FPS } from "../data/segments";
import { Background } from "./Background";
import { SubtitleBar } from "./SubtitleBar";
import { SegmentTransition } from "./SegmentTransition";

// =============================================================================
// ANIMATION IMPORTS
// =============================================================================
// Import your animation components here. The template includes a library of
// reusable F1 animations in src/animations/. Import the ones you need:
//
// import { TitleReveal } from "../animations/TitleReveal";
// import { TeamSpotlight } from "../animations/TeamSpotlight";
// import { VenetianBlinds } from "../animations/VenetianBlinds";
// import { GhostWing } from "../animations/GhostWing";
// ... etc.
//
// Or create your own animation components following the same pattern:
//   - Accept no props (segment context comes from parent)
//   - Use useCurrentFrame() and useVideoConfig() for timing
//   - Use spring() and interpolate() for smooth motion
//   - Return an <AbsoluteFill> with SVG/HTML content
// =============================================================================

import { TitleReveal } from "../animations/TitleReveal";
import { TeamSpotlight } from "../animations/TeamSpotlight";
import { QuestionBoard } from "../animations/QuestionBoard";

interface SegmentRendererProps {
  segment: Segment;
}

// =============================================================================
// ANIMATION ROUTER
// =============================================================================
// Map each animationType string to its component. Add cases for each animation
// type defined in your segments data.
const getAnimation = (segment: Segment): React.ReactNode => {
  switch (segment.animationType) {
    case "title_reveal":
      return <TitleReveal />;

    // Team spotlight — works for any team, parametric via props
    case "car_spotlight":
      return (
        <TeamSpotlight
          team={segment.team || ""}
          analogy={segment.analogy}
        />
      );

    case "question_board":
      return <QuestionBoard />;

    // =========================================================================
    // ADD YOUR ANIMATION CASES HERE
    // =========================================================================
    // case "venetian_blinds":
    //   return <VenetianBlinds />;
    // case "ghost_wing":
    //   return <GhostWing />;
    // case "suspension_exploder":
    //   return <SuspensionExploder />;
    // ... etc.

    default:
      // Fallback: team spotlight for team segments, question board for others
      if (segment.team) {
        return (
          <TeamSpotlight
            team={segment.team}
            analogy={segment.analogy}
          />
        );
      }
      return <QuestionBoard />;
  }
};

export const SegmentRenderer: React.FC<SegmentRendererProps> = ({
  segment,
}) => {
  const { fps } = useVideoConfig();
  const segmentDuration = segment.endTime - segment.startTime;
  const segmentFrames = Math.ceil(segmentDuration * fps);
  const transitionFrames = 15;

  return (
    <AbsoluteFill>
      {/* Background layer — team-colored, emotion-reactive */}
      <Background
        teamColor={segment.teamColor}
        teamAccent={segment.teamAccent}
        emotion={segment.emotion}
      />

      {/* Main animation content */}
      {getAnimation(segment)}

      {/* Subtitle bar at bottom — word-by-word reveal */}
      <SubtitleBar
        text={segment.text}
        emotion={segment.emotion}
        teamColor={segment.teamColor}
      />

      {/* Entry wipe transition */}
      <Sequence from={0} durationInFrames={transitionFrames}>
        <SegmentTransition
          teamColor={segment.teamColor || "#E10600"}
          direction="in"
          durationFrames={transitionFrames}
        />
      </Sequence>

      {/* Exit fade transition */}
      <Sequence
        from={segmentFrames - transitionFrames}
        durationInFrames={transitionFrames}
      >
        <SegmentTransition
          teamColor={segment.teamColor || "#E10600"}
          direction="out"
          durationFrames={transitionFrames}
        />
      </Sequence>
    </AbsoluteFill>
  );
};
