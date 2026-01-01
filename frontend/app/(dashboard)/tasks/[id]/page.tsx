"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import {
    DocumentProcessing,
    ContentAnalyser,
    ScriptAndVoiceovers,
    VideoGeneration,
} from "@/components/pipeline";
import client from "@/lib/sdk/client";
import { BackgroundType, PipelineData, PipelineStageStatisticsManager, VideoResolution } from "@/lib/sdk/types";
import { LoadingPage } from "@/components/LoadingPage";
import { PipelineStagesManager } from "@/components/PipelineStagesManager";
import { PipelineTaskDetails } from "@/components/PipelineTaskDetails";
import { toast } from "sonner";

export default function TaskDetailPage() {
    const params = useParams();
    const taskId = params.id as string;
    const [taskDetails, setTaskDetails] = useState<PipelineData | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const fetchTaskDetails = async () => {
        setIsLoading(true);
        const result: PipelineData = await client.getPipelineDetails(taskId);
        setTaskDetails(result);
        setIsLoading(false);
    };

    useEffect(() => {
        fetchTaskDetails().catch(console.error);
    }, [taskId]);

    const generateOutlineContent = async () => {
        // todo: add form to request the user to provide video processing information
        await client.processContent(taskId, {
            skip_stock: false,
            target_segments: 10,
            segment_duration: 10
        });
        fetchTaskDetails().catch(console.error);
    }

    const scriptAndAudioGeneration = async () => {
        await client.generateScriptsAndVoiceovers(taskId);
        fetchTaskDetails().catch(console.error);
    }

    const videoGeneration = async () => {
        // todo: add form to request the user to provide video generation information
        await client.generateVideo(taskId, {
            title: taskDetails?.name || "",
            subtitle: taskDetails?.description || "",
            resolution: VideoResolution.RESOLUTION_1080P,
            fps: 30,
            title_duration: 3.0,
            end_duration: 3.0,
            transition_duration: 0.5,
            background_type: BackgroundType.GRADIENT,
        });
        fetchTaskDetails().catch(console.error);
    }

    // utility function to download a blob in the browser
    function downloadBlob(blob: Blob, filename: string) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }, 0);
    }

    const downloadAndShare = async () => {
        const blob = await client.downloadVideo(taskId);
        if (blob) {
            downloadBlob(blob, "vidinie-video.mp4");
            // todo: add a message to the user that the video has been downloaded
            toast.success("Video downloaded successfully");
        }
    }

    return (
        <div className="p-4">
            {isLoading ? (
                <LoadingPage />
            ) : (
                <div className="flex flex-row gap-4 mx-auto">
                    <div className="w-1/3 flex flex-col gap-4">
                        <PipelineStagesManager pipelineStageStatistics={taskDetails?.stage_statistics as PipelineStageStatisticsManager} 
                            onGenerateOutlineContent={generateOutlineContent} 
                            onScriptAndAudioGeneration={scriptAndAudioGeneration} 
                            onVideoGeneration={videoGeneration} 
                            onDownloadAndShare={downloadAndShare} 
                        />
                        <PipelineTaskDetails name={taskDetails?.name || ""} description={taskDetails?.description || ""} tags={taskDetails?.tags || []} projects={taskDetails?.projects || []} />
                    </div>
                    <div className="w-2/3">
                        <div className="text-sm whitespace-pre-wrap break-words max-w-full" style={{ wordBreak: "break-word" }}>
                            <DocumentProcessing content={taskDetails?.parsed_content} images={taskDetails?.images_metadata} />
                            {taskDetails?.video_outline && (
                                <>
                                    <hr className="mt-8" />
                                    <ContentAnalyser videoOutline={taskDetails?.video_outline} />
                                </>
                            )}
                            {taskDetails?.script_data && (
                                <>
                                    <hr className="mt-8" />
                                    <ScriptAndVoiceovers 
                                        scriptData={taskDetails.script_data}
                                        fullAudioPath={taskDetails.full_audio_path}
                                        fullAudioDuration={taskDetails.full_audio_duration}
                                    />
                                </>
                            )}
                            {taskDetails?.video_path && (
                                <>
                                    <hr className="mt-8" />
                                    <VideoGeneration pipelineId={taskId} />
                                </>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
