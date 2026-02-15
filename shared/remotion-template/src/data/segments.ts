// =============================================================================
// SEGMENT DATA TEMPLATE
// =============================================================================
// This file defines the segment structure for any F1 Remotion video.
//
// TO USE: Keep the interfaces and TEAM_COLORS as-is. Replace the `segments`
// array with your project's data from the VTT transcript timestamps.
//
// WORKFLOW:
//   1. Generate audio (podcast chunks or voiceover segments)
//   2. Parse the VTT transcript for segment start/end times
//   3. Define each segment with its animation type
//   4. The composition will automatically sync animations to audio
// =============================================================================

export interface Segment {
  id: number;
  startTime: number; // seconds from video start
  endTime: number; // seconds from video start
  text: string; // voiceover text (used for subtitle display)
  context: string; // editorial note (not rendered)
  emotion: string; // energetic | intrigued | passionate | contemplative | humorous | heartfelt | excited
  team?: string; // F1 team name (keys into TEAM_COLORS)
  teamColor?: string; // override color
  teamAccent?: string; // override accent
  analogy?: string; // quotable analogy for callout display
  visualType: string; // high-level category (intro, team_deep_dive, analysis, etc.)
  animationType: string; // maps to specific animation component in SegmentRenderer
}

// F1 2026 team colors — use team name as key
export const TEAM_COLORS: Record<
  string,
  { primary: string; accent: string; gradient: string }
> = {
  "Aston Martin": {
    primary: "#006F62",
    accent: "#CEDC00",
    gradient: "from-[#006F62] to-[#004C40]",
  },
  Mercedes: {
    primary: "#27F4D2",
    accent: "#000000",
    gradient: "from-[#27F4D2] to-[#00A887]",
  },
  Williams: {
    primary: "#64C4FF",
    accent: "#041E42",
    gradient: "from-[#64C4FF] to-[#041E42]",
  },
  Alpine: {
    primary: "#FF87BC",
    accent: "#0093CC",
    gradient: "from-[#FF87BC] to-[#0093CC]",
  },
  Audi: {
    primary: "#FFFFFF",
    accent: "#E10600",
    gradient: "from-[#333333] to-[#000000]",
  },
  "Red Bull": {
    primary: "#3671C6",
    accent: "#FFD700",
    gradient: "from-[#3671C6] to-[#1B3A6B]",
  },
  McLaren: {
    primary: "#FF8000",
    accent: "#47C7FC",
    gradient: "from-[#FF8000] to-[#E85D04]",
  },
  Ferrari: {
    primary: "#E8002D",
    accent: "#FFF200",
    gradient: "from-[#E8002D] to-[#A40020]",
  },
  Haas: {
    primary: "#B6BABD",
    accent: "#E10600",
    gradient: "from-[#B6BABD] to-[#6C6C6C]",
  },
  "Racing Bulls": {
    primary: "#6692FF",
    accent: "#E10600",
    gradient: "from-[#6692FF] to-[#1B3A6B]",
  },
  Cadillac: {
    primary: "#1E3A5F",
    accent: "#C0C0C0",
    gradient: "from-[#1E3A5F] to-[#0D1B2A]",
  },
};

export const FPS = 30;

// Helper: convert mm:ss.mmm to seconds
export function t(
  minutes: number,
  seconds: number,
  millis: number = 0
): number {
  return minutes * 60 + seconds + millis / 1000;
}

// =============================================================================
// REPLACE BELOW WITH YOUR PROJECT'S DATA
// =============================================================================

// Example segment (replace with your VTT-parsed segments)
export const segments: Segment[] = [
  {
    id: 1,
    startTime: t(0, 0),
    endTime: t(0, 30),
    text: "Your opening voiceover text here...",
    context: "Intro hook",
    emotion: "energetic",
    visualType: "intro",
    animationType: "title_reveal",
  },
  // Add more segments from your VTT transcript...
];

// Audio file durations (if using chunked TTS, list each chunk)
export const AUDIO_CHUNKS = [
  { file: "chunk_000.mp3", duration: 0 },
  // Add your audio chunks...
];

// Total durations (calculate from your audio)
export const TOTAL_DURATION = 60; // seconds of voice content
export const VIDEO_DURATION = 60; // total video length including any padding
