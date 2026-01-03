"use client";

import { VideoPlayer } from "@/components/utils/VideoPlayer";

interface VideoGenerationProps {
    videoPipelineId: string;
}

export function VideoGeneration({ videoPipelineId }: VideoGenerationProps) {
    return (
        <div className="space-y-8 pt-8">
            <div className="max-w-4xl mx-auto">
                <div className="space-y-4 mb-4">
                    <h3 className="font-semibold text-sm">Generated Video</h3>
                    <VideoPlayer videoPipelineId={videoPipelineId} />
                </div>
            </div>
        </div>
    );
}
