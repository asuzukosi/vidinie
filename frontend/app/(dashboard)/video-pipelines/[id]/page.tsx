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
import { VideoPipeline, VideoPipelineStage, GenerateVideoPipelineRequest, CreateVideoPipelineOutlineRequest, VideoPipelineReviewRequest } from "@/lib/sdk/types";
import { LoadingPage } from "@/components/utils/LoadingPage";
import { VideoPipelineStagesManager } from "@/components/pipeline/VideoPipelineStagesManager";
import { VideoPipelineDetails } from "@/components/pipeline/VideoPipelineDetails";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function TaskDetailPage() {
    const params = useParams();
    const taskId = params.id as string;
    const [taskDetails, setTaskDetails] = useState<VideoPipeline | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedStage, setSelectedStage] = useState<VideoPipelineStage | null>(VideoPipelineStage.DOCUMENT_PROCESSING);
    const [isProcessingContent, setIsProcessingContent] = useState(false);
    const [isGeneratingScripts, setIsGeneratingScripts] = useState(false);
    const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);
    const [isSubmittingReview, setIsSubmittingReview] = useState(false);

    const fetchTaskDetails = async () => {
        setIsLoading(true);
        const result: VideoPipeline = await client.getVideoPipelineDetails(taskId);
        setTaskDetails(result);
        setIsLoading(false);
    };

    useEffect(() => {
        fetchTaskDetails().catch(console.error);
    }, [taskId]);

    const generateOutlineContent = async (data: CreateVideoPipelineOutlineRequest) => {
        setIsProcessingContent(true);
        try {
            await client.processVideoPipelineContent(taskId, data);
            await fetchTaskDetails();
        } catch (error) {
            console.error("Error generating outline content:", error);
            toast.error("Failed to generate outline content");
        } finally {
            setIsProcessingContent(false);
        }
    }

    const scriptAndAudioGeneration = async () => {
        setIsGeneratingScripts(true);
        try {
            await client.generateVideoPipelineScripts(taskId);
            await fetchTaskDetails();
        } catch (error) {
            console.error("Error generating scripts and voiceovers:", error);
            toast.error("Failed to generate scripts and voiceovers");
        } finally {
            setIsGeneratingScripts(false);
        }
    }

    const videoGeneration = async (data: GenerateVideoPipelineRequest) => {
        setIsGeneratingVideo(true);
        try {
            await client.generateVideoPipelineOutput(taskId, data);
            await fetchTaskDetails();
        } catch (error) {
            console.error("Error generating video:", error);
            toast.error("Failed to generate video");
        } finally {
            setIsGeneratingVideo(false);
        }
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

    const reviewAndFeedback = async (data: VideoPipelineReviewRequest) => {
        setIsSubmittingReview(true);
        try {
            await client.addVideoPipelineReview(taskId, data);
            await fetchTaskDetails();
            toast.success("Review submitted successfully");
        } catch (error) {
            console.error("Error submitting review:", error);
            toast.error("Failed to submit review");
        } finally {
            setIsSubmittingReview(false);
        }
    }

    const shouldShowSection = (stage: VideoPipelineStage) => {
        // if no stage is selected, default to showing document processing
        const stageToShow = selectedStage || VideoPipelineStage.DOCUMENT_PROCESSING;
        return stageToShow === stage;
    };

    return (
        <div className="p-4">
            {isLoading ? (
                <LoadingPage />
            ) : (
                <div className="flex flex-row gap-6 mx-auto">
                    <div className="w-1/3 flex flex-col gap-4">
                        <VideoPipelineStagesManager 
                            pipelineStageStatuses={taskDetails?.stage_statuses || {}} 
                            onGenerateOutlineContent={generateOutlineContent} 
                            onScriptAndAudioGeneration={scriptAndAudioGeneration} 
                            onVideoGeneration={videoGeneration} 
                            onReviewAndFeedback={reviewAndFeedback}
                            onStageSelect={(stage) => setSelectedStage(stage)}
                            selectedStage={selectedStage}
                            defaultVideoTitle={taskDetails?.name || ""}
                            defaultVideoSubtitle={taskDetails?.description || ""}
                            isProcessingContent={isProcessingContent}
                            isGeneratingScripts={isGeneratingScripts}
                            isGeneratingVideo={isGeneratingVideo}
                            isSubmittingReview={isSubmittingReview}
                        />
                        <VideoPipelineDetails name={taskDetails?.name || ""} description={taskDetails?.description || ""} tags={taskDetails?.tags || []} projects={taskDetails?.projects || []} />
                    </div>
                    <div className="w-2/3 flex flex-col gap-6">
                        {shouldShowSection(VideoPipelineStage.DOCUMENT_PROCESSING) && (
                            <Card>
                                <CardHeader>
                                    <CardTitle>Document Processing</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <DocumentProcessing content={taskDetails?.parsed_content} images={taskDetails?.images_metadata} />
                                </CardContent>
                            </Card>
                        )}
                        {shouldShowSection(VideoPipelineStage.CONTENT_ANALYSIS) && taskDetails?.video_outline && (
                            <Card>
                                <CardHeader>
                                    <CardTitle>Content Analysis</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <ContentAnalyser videoOutline={taskDetails?.video_outline} />
                                </CardContent>
                            </Card>
                        )}
                        {shouldShowSection(VideoPipelineStage.SCRIPT_GENERATION) && taskDetails?.script_data && (
                            <Card>
                                <CardHeader>
                                    <CardTitle>Script and Audio Generation</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <ScriptAndVoiceovers 
                                        scriptData={taskDetails.script_data}
                                        fullAudioPath={taskDetails.full_audio_path}
                                        fullAudioDuration={taskDetails.full_audio_duration}
                                    />
                                </CardContent>
                            </Card>
                        )}
                        {shouldShowSection(VideoPipelineStage.VIDEO_GENERATION) && taskDetails?.video_path && (
                            <Card>
                                <CardHeader>
                                    <CardTitle>Video Generation</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <VideoGeneration videoPipelineId={taskId} />
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
