import { Badge } from "@/components/ui/badge";
import { VideoPipelineStage } from "@/lib/sdk/types";

interface VideoPipelineStageBadgeProps {
  stage: VideoPipelineStage;
}

export function VideoPipelineStageBadge({ stage }: VideoPipelineStageBadgeProps) {
  switch (stage) {
    case VideoPipelineStage.INITIALIZED:
      return (
        <Badge
          variant="outline"
          className="bg-amber-500/15 text-amber-700 hover:bg-amber-500/25 dark:bg-amber-500/10 dark:text-amber-300 dark:hover:bg-amber-500/20 border-0"
        >
          Initialized
        </Badge>
      );
    case VideoPipelineStage.DOCUMENT_PROCESSING:
      return (
        <Badge
          variant="outline"
          className="bg-blue-500/15 text-blue-700 hover:bg-blue-500/25 dark:bg-blue-500/10 dark:text-blue-400 dark:hover:bg-blue-500/20 border-0"
        >
          Document Processing
        </Badge>
      );
    case VideoPipelineStage.IMAGE_PROCESSING:
      return (
        <Badge
          variant="outline"
          className="bg-blue-500/15 text-blue-700 hover:bg-blue-500/25 dark:bg-blue-500/10 dark:text-blue-400 dark:hover:bg-blue-500/20 border-0"
        >
          Image Processing
        </Badge>
      );
    case VideoPipelineStage.CONTENT_ANALYSIS:
      return (
        <Badge
          variant="outline"
          className="bg-blue-500/15 text-blue-700 hover:bg-blue-500/25 dark:bg-blue-500/10 dark:text-blue-400 dark:hover:bg-blue-500/20 border-0"
        >
          Content Analysis
        </Badge>
      );
    case VideoPipelineStage.SCRIPT_GENERATION:
      return (
        <Badge
          variant="outline"
          className="bg-blue-500/15 text-blue-700 hover:bg-blue-500/25 dark:bg-blue-500/10 dark:text-blue-400 dark:hover:bg-blue-500/20 border-0"
        >
          Script Generation
        </Badge>
      );
    case VideoPipelineStage.VIDEO_GENERATION:
      return (
        <Badge
          variant="outline"
          className="bg-blue-500/15 text-blue-700 hover:bg-blue-500/25 dark:bg-blue-500/10 dark:text-blue-400 dark:hover:bg-blue-500/20 border-0"
        >
          Video Generation
        </Badge>
      );
    default:
      return <Badge variant="secondary">{stage}</Badge>;
  }
}

