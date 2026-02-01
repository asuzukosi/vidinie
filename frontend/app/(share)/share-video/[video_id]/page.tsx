"use client";

import { useParams } from "next/navigation";
import { VideoPlayer } from "@/components/utils/video-player";
import { PostHogEvent } from "@/lib/utils";
import { useEffect } from "react";
import posthog from 'posthog-js';

export default function ShareVideoPage() {
  const params = useParams();
  const videoId = params.video_id as string;

  useEffect(() => {
    posthog.capture(PostHogEvent.SHARE_VIDEO_PAGE_VIEWED, {
      category: "share_video",
      label: videoId,
      value: 1,
    });
  }, [videoId]);

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-black flex items-center justify-center p-4">
      <div className="w-full max-w-6xl aspect-video">
        <VideoPlayer videoPipelineId={videoId} />
      </div>
    </div>
  );
}

