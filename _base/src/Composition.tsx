/**
 * Main video composition - imports and sequences all segments
 * 
 * PATTERN:
 * 1. Import all segment components: Segment1, Segment2, Segment3, etc.
 * 2. Calculate segment durations: audio_duration × 15 fps (NOT estimated duration - audio is source of truth)
 * 3. Use Sequence components to chain segments seamlessly
 * 4. Segments connect end-to-end: Segment2 starts where Segment1 ends
 * 
 * EXAMPLE:
 * const segment1Duration = 570; // audio_duration × 15fps (e.g., 38s × 15 = 570)
 * const segment2Duration = 630; // audio_duration × 15fps (e.g., 42s × 15 = 630)
 * 
 * <Sequence from={0} durationInFrames={segment1Duration}>
 *   <Segment1 />
 * </Sequence>
 * <Sequence from={segment1Duration} durationInFrames={segment2Duration}>
 *   <Segment2 />
 * </Sequence>
 * 
 * ⚠️ CRITICAL: Segments connect seamlessly - no gaps | Audio crossfade: 5-10 frame overlap
 * ⚠️ CRITICAL: Each segment handles fade in/out in first/last 10-15 frames
 * ⚠️ CRITICAL: Background music plays continuously throughout entire video
 */
import { AbsoluteFill, Audio, Img, Sequence, staticFile } from 'remotion';
// Import your segments here:
// import { Segment1 } from './segments/Segment1';
// import { Segment2 } from './segments/Segment2';

export const MyComposition = () => {
  // Calculate segment durations (audio_duration × 15 fps)
  // const segment1Duration = 0; // Update based on audio length
  // const segment2Duration = 0; // Update based on audio length

  return (
    <AbsoluteFill>
      {/* Background music - plays throughout entire video at 15% volume */}
      <Audio src={staticFile('music/background_music.mp3')} volume={0.15} />

      {/* Add segments here using Sequence components */}
      {/* Example:
      <Sequence from={0} durationInFrames={segment1Duration}>
        <Segment1 />
      </Sequence>
      <Sequence from={segment1Duration} durationInFrames={segment2Duration}>
        <Segment2 />
      </Sequence>
      */}

      {/* CRITICAL: WATERMARK - Vidinie logo + white text "made with vidinie.com" in bottom right corner */}
      {/* Must appear on ALL segments - fixed position, small size (slightly smaller), subtle opacity */}
      {/* Text is white, NOT a clickable link - just plain text below logo */}
      {/* Example:
      <div style={{
        position: 'absolute',
        bottom: 15,
        right: 15,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-end',
        opacity: 0.8,
        zIndex: 1000
      }}>
        <Img src={staticFile('vidinie.png')} style={{ width: 35, height: 'auto' }} />
        <div style={{ fontSize: 11, color: '#ffffff', marginTop: 4 }}>made with vidinie.com</div>
      </div>
      */}
    </AbsoluteFill>
  );
};
