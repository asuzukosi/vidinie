import "./index.css";
import { Composition } from "remotion";
import { MyComposition } from "./Composition";

/**
 * Root composition configuration
 * 
 * ⚠️ DO NOT MODIFY:
 * - id="VidinieComposition" (fixed)
 * - component={MyComposition} (fixed)
 * - fps={15} (fixed for 480p)
 * - width={854} (fixed for 480p)
 * - height={480} (fixed for 480p)
 * 
 * ✅ ONLY MODIFY:
 * - durationInFrames: Calculate as total_seconds × 15 (fps)
 *   Example: 240 seconds = 240 × 15 = 3600 frames
 */
export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="VidinieComposition" 
        component={MyComposition}
        durationInFrames={60} // ⚠️ UPDATE THIS: total_seconds × 15
        fps={15}
        width={854}
        height={480}
      />
    </>
  );
};
