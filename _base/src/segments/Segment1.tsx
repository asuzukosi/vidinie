/**
 * Segment component template
 * 
 * See prompts for detailed guidance on:
 * - Component structure and imports
 * - Opacity animation patterns with staggered fade outs
 * - Audio synchronization and timing
 * - Design principles (visual aesthetics, beauty, enjoyability)
 * - Layout and spatial distribution
 * - Animation coordination to prevent overlaps
 */
import { AbsoluteFill, Audio, Img, interpolate, useCurrentFrame, staticFile } from 'remotion';
// ⚠️ Use safe fonts only: Poppins, Montserrat, Roboto, Raleway, OpenSans, Lato, Inter, RobotoSlab, PlayfairDisplay, Lobster, BebasNeue, Oswald, Nunito, WorkSans
// import { loadFont } from '@remotion/google-fonts/Poppins';

// ⚠️ ALWAYS specify weights and subsets to prevent excessive network requests
// const { fontFamily } = loadFont("normal", { weights: ["400", "700"], subsets: ["latin"] });

export const Segment1: React.FC = () => {
  const frame = useCurrentFrame();
  // Replace with actual segment duration
  const segmentDuration = 570; // Calculate: audio_length_seconds × 15

  // Fade in title in first 10-15 frames
  // const titleOpacity = interpolate(frame, [0, 15, segmentDuration-15, segmentDuration], [0, 1, 1, 0], { extrapolateRight: 'clamp' });

  // Fade out content in last 10-15 frames (staggered)
  // const text1Opacity = interpolate(frame, [60, 80, segmentDuration-20, segmentDuration-15], [0, 1, 1, 0], { extrapolateRight: 'clamp' });
  // const text2Opacity = interpolate(frame, [150, 170, segmentDuration-10, segmentDuration-5], [0, 1, 1, 0], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ backgroundColor: '#0a0a0a' }}>
      {/* Background - use Img or Video, add transparent overlay if needed */}
      {/* <Img src={staticFile('images/stock_images/example.jpg')} style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> */}
      {/* <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', background: 'linear-gradient(to bottom, rgba(0,0,0,0.4), rgba(0,0,0,0.7))' }} /> */}

      {/* Title - fade in first 10-15 frames, fade out last 10-15 frames */}
      {/* <div style={{ position: 'absolute', top: 30, left: 30, right: 30, opacity: titleOpacity }}>
        <h1 style={{ fontFamily, fontSize: 28, fontWeight: 700, color: '#ffffff', margin: 0 }}>Title</h1>
      </div> */}

      {/* Content text - stagger fade outs to prevent overlap */}
      {/* <div style={{ position: 'absolute', bottom: 30, left: 30, right: 30 }}>
        <p style={{ fontFamily, fontSize: 16, color: '#ffffff', margin: 0, opacity: text1Opacity }}>Text 1</p>
        <p style={{ fontFamily, fontSize: 16, color: '#ffffff', margin: 0, opacity: text2Opacity }}>Text 2</p>
      </div> */}

      {/* Segment audio */}
      {/* <Audio src={staticFile('audio/segment_00_Your Segment Name.mp3')} /> */}
    </AbsoluteFill>
  );
};
