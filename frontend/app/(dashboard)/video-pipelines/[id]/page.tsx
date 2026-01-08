"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import {
    DocumentProcessing,
    ContentAnalyser,
    ScriptAndVoiceovers,
    VideoGeneration,
} from "@/components/pipeline";
import client from "@/lib/sdk/client";
import { VideoPipeline, VideoPipelineStage, GenerateVideoPipelineRequest, CreateVideoPipelineOutlineRequest, VideoPipelineReviewRequest, VideoPipelineStatus } from "@/lib/sdk/types";
import { LoadingPage } from "@/components/utils/LoadingPage";
import { VideoPipelineStagesManager } from "@/components/pipeline/VideoPipelineStagesManager";
import { VideoPipelineDetails } from "@/components/pipeline/VideoPipelineDetails";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function TaskDetailPage() {
    const params = useParams();
    const router = useRouter();
    const taskId = params.id as string;
    const [videoPipeline, setVideoPipeline] = useState<VideoPipeline | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedStage, setSelectedStage] = useState<VideoPipelineStage | null>(VideoPipelineStage.DOCUMENT_PROCESSING);
    const [isProcessingContent, setIsProcessingContent] = useState(false);
    const [isGeneratingScripts, setIsGeneratingScripts] = useState(false);
    const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);
    const [isSubmittingReview, setIsSubmittingReview] = useState(false);

    const fetchVideoPipeline = async () => {
        setIsLoading(true);
        try {
            const result: VideoPipeline = await client.getVideoPipelineDetails(taskId);
            setVideoPipeline(result);
            setIsProcessingContent(result.stage_statuses?.[VideoPipelineStage.CONTENT_ANALYSIS] === VideoPipelineStatus.IN_PROGRESS);
            setIsGeneratingScripts(result.stage_statuses?.[VideoPipelineStage.SCRIPT_GENERATION] === VideoPipelineStatus.IN_PROGRESS);
            setIsGeneratingVideo(result.stage_statuses?.[VideoPipelineStage.VIDEO_GENERATION] === VideoPipelineStatus.IN_PROGRESS);
        } catch (error) {
            console.error("Error fetching video pipeline:", error);
            toast.error(`Failed to retrieve video pipeline with id: ${taskId}`);
            setVideoPipeline(null);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchVideoPipeline();
    }, [taskId]);

    const generateOutlineContent = async (data: CreateVideoPipelineOutlineRequest) => {
        setIsProcessingContent(true);
        try {
            await client.processVideoPipelineContent(taskId, data);
            await fetchVideoPipeline();
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
            await fetchVideoPipeline();
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
            await fetchVideoPipeline();
        } catch (error) {
            console.error("Error generating video:", error);
            toast.error("Failed to generate video");
        } finally {
            setIsGeneratingVideo(false);
        }
    }

    const reviewAndFeedback = async (data: VideoPipelineReviewRequest) => {
        setIsSubmittingReview(true);
        try {
            await client.addVideoPipelineReview(taskId, data);
            await fetchVideoPipeline();
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

    if (isLoading) {
        return (
            <div className="p-4">
                <LoadingPage />
            </div>
        );
    }

    if (!videoPipeline) {
        return (
            <div className="p-4 flex items-center justify-center min-h-[calc(100vh-4rem)]">
                <Card className="w-full max-w-md">
                    <CardHeader>
                        <CardTitle>Video Pipeline Not Found</CardTitle>
                        <CardDescription>
                            Video pipeline specified not found, failed to retrieve video pipeline
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Button 
                            onClick={() => router.push("/video-pipelines")}
                            className="w-full"
                        >
                            Back to Video Pipelines
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }
    return (
        <div className="p-4">
            <div className="flex flex-row gap-6 mx-auto">
                <div className="w-1/3 flex flex-col gap-4">
                    <VideoPipelineStagesManager 
                        pipelineStageStatuses={videoPipeline.stage_statuses || {}} 
                        onGenerateOutlineContent={generateOutlineContent} 
                        onScriptAndAudioGeneration={scriptAndAudioGeneration} 
                        onVideoGeneration={videoGeneration} 
                        onStageSelect={(stage) => setSelectedStage(stage)}
                        selectedStage={selectedStage}
                        defaultVideoTitle={videoPipeline.name}
                        defaultVideoSubtitle={videoPipeline.description}
                        isProcessingContent={isProcessingContent}
                        isGeneratingScripts={isGeneratingScripts}
                        isGeneratingVideo={isGeneratingVideo}
                    />
                    <VideoPipelineDetails 
                        name={videoPipeline.name} 
                        description={videoPipeline.description} 
                        tags={videoPipeline.tags} 
                        projects={videoPipeline.projects}
                        created_at={videoPipeline.created_at}
                        current_stage={videoPipeline.current_stage}
                        status={videoPipeline.status}
                    />
                </div>
                <div className="w-2/3 flex flex-col gap-6">
                    {shouldShowSection(VideoPipelineStage.DOCUMENT_PROCESSING) && (
                        <Card>
                            <CardHeader>
                                <CardTitle>Document Processing</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <DocumentProcessing 
                                    content={videoPipeline.parsed_content} 
                                    images={videoPipeline.images_metadata}
                                    videoPipelineId={taskId}
                                    onRefresh={fetchVideoPipeline}
                                />
                            </CardContent>
                        </Card>
                    )}
                    {shouldShowSection(VideoPipelineStage.CONTENT_ANALYSIS) && (
                        <Card>
                            <CardHeader>
                                <CardTitle>Content Analysis</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ContentAnalyser 
                                    videoOutline={videoPipeline.video_outline} 
                                    onGenerateOutlineContent={generateOutlineContent}
                                    isProcessingContent={isProcessingContent}
                                />
                            </CardContent>
                        </Card>
                    )}
                    {shouldShowSection(VideoPipelineStage.SCRIPT_GENERATION) && (
                        <Card>
                            <CardHeader>
                                <CardTitle>Script and Audio Generation</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ScriptAndVoiceovers 
                                    scriptData={videoPipeline.script_data}
                                    fullAudioPath={videoPipeline.full_audio_path}
                                    fullAudioDuration={videoPipeline.full_audio_duration}
                                    onScriptAndAudioGeneration={scriptAndAudioGeneration}
                                    isGeneratingScripts={isGeneratingScripts}
                                />
                            </CardContent>
                        </Card>
                    )}
                    {shouldShowSection(VideoPipelineStage.VIDEO_GENERATION) && (
                        <Card>
                            <CardHeader>
                                <CardTitle>Video Generation</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <VideoGeneration 
                                    videoPipelineId={taskId}
                                    videoPath={videoPipeline.video_path}
                                    rating={videoPipeline.rating}
                                    feedback={videoPipeline.feedback}
                                    updated_at={videoPipeline.updated_at}
                                    onVideoGeneration={videoGeneration}
                                    onReviewAndFeedback={reviewAndFeedback}
                                    isGeneratingVideo={isGeneratingVideo}
                                    isSubmittingReview={isSubmittingReview}
                                    defaultVideoTitle={videoPipeline.name}
                                    defaultVideoSubtitle={videoPipeline.description}
                                />
                            </CardContent>
                        </Card>
                    )}
                </div>
            </div>
        </div>
    );
}
