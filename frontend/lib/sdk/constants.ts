import { VideoPipelineProcessingStage, VideoPipelineStage } from "./types";

export const pipelineProcessingStages: VideoPipelineProcessingStage[] = [
    {
      id: VideoPipelineStage.DOCUMENT_PROCESSING,
      title: "Document Processing",
      description: "Processing the document to extract the content and images. We will extract the content and save it to the database.",
      completed: false,
      actionLabel: "Process document",
    },
    {
      id: VideoPipelineStage.CONTENT_ANALYSIS,
      title: "Content Analysis",
      description: "Analyzing the content for the video. We will analyze the content and save it to the database.",
      completed: false,
      actionLabel: "Analyze content",
    },
    {
      id: VideoPipelineStage.SCRIPT_GENERATION,
      title: "Script and Audio Generation",
      description: "Generating the script and audio for the video. We will generate the script and audio and save it to the database.",
      completed: false,
      actionLabel: "Generate script and audio",
    },
    {
      id: VideoPipelineStage.VIDEO_GENERATION,
      title: "Video Generation",
      description: "Generating the video for the content. We will generate the video and save it to the database.",
      completed: false,
      actionLabel: "Generate video",
    },
    {
      id: VideoPipelineStage.REVIEW_AND_FEEDBACK,
      title: "Review and Feedback",
      description: "Share your feedback about the video pipeline. Your rating and comments help us improve.",
      completed: false,
      actionLabel: "Submit review",
    },
  ];