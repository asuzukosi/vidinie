import "./index.css";
import { Composition } from "remotion";
import { MyComposition } from "./Composition";

// DO NOT MODIFY THE FOLLOWING PARAMETERS
// DO NOT MODIFY THE ID OF THE COMPOSITION
// DO NOT CHANGE THE COMPONEENT MODIFY THE Composition.tsx file
// WIDTH MUST BE 854 AND HEIGHT MUST BE 480 FOR 480P RESOLUTION
// FPS MUST BE 15 FOR 480P RESOLUTION
// THE ONLHY FIELD THAT IS MODIFIABLE IS THE DURATION IN FRAMES AS THIS IS CALCULATED BASED ON THE GENERAGTED VIDEO
export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="VidinieComposition" 
        component={MyComposition}
        durationInFrames={60}
        fps={15}
        width={854}
        height={480}
      />
    </>
  );
};
