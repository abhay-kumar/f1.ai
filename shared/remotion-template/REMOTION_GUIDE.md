# Remotion Animated Video Guide

## Overview

This template creates fully animated long-form videos using Remotion (React-based video framework). Instead of YouTube footage or stock images, every visual is programmatically animated — SVG physics diagrams, airflow particles, exploded-view breakdowns, team-colored data panels, etc.

**Best for:** Technical explainer content, aerodynamics breakdowns, regulation analysis — anything where animated diagrams explain concepts better than footage.

**Not ideal for:** Race highlights, driver interviews, or content that needs real video footage (use `image_video_assembler.py` or `video_assembler_longform.py` instead).

## Quick Start

```bash
# 1. Clone template into your project
cp -r shared/remotion-template projects/{name}/video
cd projects/{name}/video
npm install

# 2. Prepare audio
# Concatenate your audio chunks into a single file:
ffmpeg -f concat -safe 0 -i <(for f in ../audio/chunk_*.mp3; do echo "file '$PWD/../audio/$(basename $f)'"; done) -c:a libmp3lame -b:a 256k public/audio.mp3

# 3. Parse VTT transcript into segment data
# Edit src/data/segments.ts with timestamps from ../output/transcript.vtt

# 4. Wire up animations in src/components/SegmentRenderer.tsx

# 5. Preview in browser
npm run dev

# 6. Render
npm run render        # 1080p H.264
npm run build:4k      # 4K
npm run preview       # First 3 seconds only (test)
```

## Architecture

```
src/
├── index.ts                    # Entry point (registerRoot)
├── Root.tsx                    # Composition registration (HD + 4K)
├── VideoComposition.tsx        # Main composition (audio + segment sequences)
├── style.css                   # Fonts + Tailwind
├── data/
│   └── segments.ts             # Segment timing, team colors, animation types
├── components/
│   ├── Background.tsx          # Animated team-colored background (reusable)
│   ├── SubtitleBar.tsx         # Word-by-word subtitle reveal (reusable)
│   ├── SegmentTransition.tsx   # Wipe/fade transitions (reusable)
│   └── SegmentRenderer.tsx     # Animation router (customize per project)
└── animations/                 # Animation component library
    ├── TitleReveal.tsx          # F1-branded title card
    ├── TeamSpotlight.tsx        # Parametric team deep-dive
    ├── VenetianBlinds.tsx       # Wing mechanics with drag/downforce meters
    ├── SuspensionExploder.tsx   # Exploded-view component breakdown
    ├── GhostWing.tsx            # Side-by-side wing comparison
    ├── SidepodComparison.tsx    # A-vs-B airflow visualization
    ├── TransitionMoment.tsx     # Mode-switching with live gauges
    └── ... (15+ components)
```

## How It Works

### Frame-Based Rendering
Remotion renders each frame as a React component screenshot via headless Chromium, then encodes to video with FFmpeg. At 30fps, a 17-minute video = 31,410 frames.

### Audio Sync
The VTT transcript provides precise timestamps for each segment. These map to Remotion `<Sequence>` components:

```tsx
// Each segment becomes a timed Sequence
<Sequence from={startFrame} durationInFrames={duration}>
  <SegmentRenderer segment={segment} />
</Sequence>
```

### Animation Patterns
Every animation uses these Remotion primitives:

```tsx
const frame = useCurrentFrame();        // Current frame number
const { fps } = useVideoConfig();       // 30fps
const phaseTime = frame / fps;          // Current time in seconds

// Smooth entrance
const entrance = spring({ frame, fps, config: { damping: 14 } });

// Value interpolation
const opacity = interpolate(frame, [0, 30], [0, 1], {
  extrapolateRight: "clamp",
});

// Cycling/pulsing
const pulse = interpolate(Math.sin(frame / 15), [-1, 1], [0.5, 1]);
```

## Creating New Animations

### Pattern: SVG Physics Diagram

```tsx
export const MyDiagram: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const phaseTime = frame / fps;

  // Phase-based animation: intro (0-3s) → main (3-8s) → detail (8s+)
  const detailReveal = interpolate(phaseTime, [8, 10], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <svg width="900" height="400" viewBox="0 0 900 400">
        {/* Your SVG content with animated transforms/opacities */}
      </svg>
    </AbsoluteFill>
  );
};
```

### Pattern: Airflow Particles

```tsx
const particles = Array.from({ length: 15 }, (_, i) => {
  const speed = 1.5 + (i % 3) * 0.4;
  const x = ((frame * speed + i * 45) % 700) + 150;
  const y = 280 + Math.sin(i * 1.3) * 20;
  return { x, y };
});

// In SVG:
{particles.map((p, i) => (
  <circle key={i} cx={p.x} cy={p.y} r={2.5} fill="#27F4D2" opacity={0.5} />
))}
```

### Pattern: Staggered Card Reveals

```tsx
const items = ["Item 1", "Item 2", "Item 3"];
{items.map((item, i) => {
  const cardSpring = spring({
    frame: frame - i * fps * 1.5,  // 1.5s stagger
    fps,
    config: { damping: 14 },
  });
  return (
    <div style={{
      opacity: interpolate(cardSpring, [0, 1], [0, 1]),
      transform: `translateX(${interpolate(cardSpring, [0, 1], [-30, 0])}px)`,
    }}>
      {item}
    </div>
  );
})}
```

## Animation Library Reference

| Component | Use Case | Key Props/Features |
|---|---|---|
| `TitleReveal` | Video intro | Checkered flag, speed lines, title + subtitle reveal |
| `TeamSpotlight` | Any team segment | `team`, `carName`, `headline`, `stats[]`, `analogy` |
| `TeamRecap` | Multi-team summary | 8-team grid with sequential spotlight |
| `QuestionBoard` | Analysis/comparison | Question cards with team color pills |
| `VenetianBlinds` | Wing/aero mechanics | Animated wing flaps, drag/downforce meters |
| `SuspensionExploder` | Component breakdown | Parts explode outward, labels appear |
| `GhostWing` | Side-by-side comparison | Two mechanisms compared simultaneously |
| `SidepodComparison` | A-vs-B airflow | Conventional vs unconventional with particles |
| `NoseChannel` | Hidden detail reveal | Trade-off panel, progressive reveal |
| `HiddenReveal` | Secret/classified reveal | "CLASSIFIED" covers lift to show hidden content |
| `AudiTransform` | Before→After morph | Progress bar, morphing shapes |
| `FighterJetInlet` | Technical callouts | Sequential detail callouts with leader lines |
| `DiffuserCutaway` | Sealed/constrained system | Blocked vs allowed airflow paths |
| `FloorTriangle` | Stacked elements | Elements appear one-by-one, form pattern |
| `RainTest` | Weather effects | Animated rain, spray particles |
| `TransitionMoment` | Mode switching | Cycling between states with force gauges |
| `EngineeringMontage` | Emotional/human | Vignette cards with icons |
| `RealityCheck` | Caveats/warnings | Warning-styled sequential cards |
| `CarEvolution` | Timeline/eras | Era comparison with diversity meter |
| `WingMechanics` | Constraint visualization | Regulation box + engineering solution |

## Rendering

### Performance Tips
- **concurrency 4** is safe for most machines (8 Chromium instances can OOM on 16GB RAM)
- **ProRes** encodes faster than H.264 during render, but produces huge files (~10GB for 17min). Transcode to H.264 afterward with VideoToolbox GPU:
  ```bash
  ffmpeg -i output.mov -c:v h264_videotoolbox -b:v 12M -c:a aac output.mp4
  ```
- **Preview first**: Always render 3 seconds (`npm run preview`) before full render
- **Render time**: ~15min for 17min video at 1080p with 4x concurrency on M-series Mac

### Rendering Commands
```bash
# Quick preview (first 3 seconds)
npx remotion render F1Video --frames=0-90 --output /tmp/preview.mp4

# Full HD render
npx remotion render F1Video --output output/final.mp4 --codec h264 --concurrency 4 --video-bitrate 12M

# Background render (won't block terminal)
nohup npx remotion render F1Video --output output/final.mp4 --codec h264 --concurrency 4 > /tmp/render.log 2>&1 &
tail -f /tmp/render.log  # Monitor progress

# 4K render
npx remotion render F1Video4K --output output/final-4k.mp4 --codec h264 --video-bitrate 20M
```

## Segment Data Workflow

### From Podcast Script to Animated Video

1. **Start with script.json** — Your podcast/video script with segments
2. **Generate audio** — `gemini_podcast_audio_generator.py --chunked`
3. **Get transcript** — The generator produces `output/transcript.vtt`
4. **Parse VTT timestamps** — Each VTT cue maps to a segment's `startTime`/`endTime`
5. **Choose animation types** — For each segment, pick from the animation library
6. **Concatenate audio** — Merge chunks into `public/audio.mp3`
7. **Preview and iterate** — `npm run dev` opens Remotion Studio
8. **Render** — `npm run render`

### VTT to Segment Data

```
00:00:00.000 --> 00:00:41.629    →    startTime: t(0, 0), endTime: t(0, 41, 629)
00:00:41.629 --> 00:01:32.994    →    startTime: t(0, 41, 629), endTime: t(1, 32, 994)
```

Use the `t(minutes, seconds, millis)` helper in segments.ts.
