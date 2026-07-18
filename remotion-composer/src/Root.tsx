import { Composition, CalculateMetadataFunction } from "remotion";
import { loadFont } from "@remotion/google-fonts/PatrickHand";
import { NexusVideo, NexusVideoProps } from "./NexusVideo";

const { fontFamily } = loadFont();

const calculateNexusMetadata: CalculateMetadataFunction<NexusVideoProps> = async ({
  props,
}) => {
  const total = props.total_duration_seconds || 0;
  return { durationInFrames: Math.ceil((total + 1) * 30) };
};

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="NexusVideo"
        component={NexusVideo}
        durationInFrames={30 * 60}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          total_duration_seconds: 60,
          audio: { voiceover: "", music: "", music_volume: 0 },
          scenes: [],
        }}
        calculateMetadata={calculateNexusMetadata}
      />
    </>
  );
};
