import { PipelineProcessingStage } from "./types";

export const pipelineProcessingStages: PipelineProcessingStage[] = [
    {
      id: "document_processing",
      title: "Document Processing",
      description: "Processing the document to extract the content and images. We will extract the content and save it to the database.",
      completed: false,
      actionLabel: "Process document",
      actionHref: "#",
    },
    {
      id: "generate_content",
      title: "Generate Content",
      description: "Generating the content for the video. We will generate the content and save it to the database.",
      completed: false,
      actionLabel: "Generate content",
      actionHref: "#",
    },
    {
      id: "script_and_audio_generation",
      title: "Script and Audio Generation",
      description: "Generating the script and audio for the video. We will generate the script and audio and save it to the database.",
      completed: false,
      actionLabel: "Generate script and audio",
      actionHref: "#",
    },
    {
      id: "video_generation",
      title: "Video Generation",
      description: "Generating the video for the content. We will generate the video and save it to the database.",
      completed: false,
      actionLabel: "Generate video",
      actionHref: "#",
    },
    {
      id: "download_and_share",
      title: "Download and Share",
      description: "Downloading the video and sharing it. We will download the video and share it with the user.",
      completed: false,
      actionLabel: "Download and share",
      actionHref: "#",
    },
  ];