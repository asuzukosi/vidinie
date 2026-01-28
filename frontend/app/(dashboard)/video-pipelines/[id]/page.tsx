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
import { VideoPipeline, VideoPipelineStage, GenerateVideoPipelineRequest, CreateVideoOutlineRequest, VideoPipelineReviewRequest, VideoPipelineStatus } from "@/lib/sdk/types";
import { LoadingPage } from "@/components/utils/loading-page";
import { VideoPipelineStagesManager } from "@/components/pipeline/video-pipeline-stages-manager";
import { VideoPipelineDetails } from "@/components/pipeline/video-pipeline-details";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useSelector } from "react-redux";
import { RootState } from "@/lib/store/store";

export default function TaskDetailPage() {
    const params = useParams();
    const router = useRouter();
    const taskId = params.id as string;
    const user = useSelector((state: RootState) => state.auth.user);
    const [videoPipeline, setVideoPipeline] = useState<VideoPipeline | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedStage, setSelectedStage] = useState<VideoPipelineStage | null>(VideoPipelineStage.DOCUMENT_PROCESSING);
    const [isProcessingDocument, setIsProcessingDocument] = useState(false);
    const [isProcessingContent, setIsProcessingContent] = useState(false);
    const [isGeneratingScripts, setIsGeneratingScripts] = useState(false);
    const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);
    const [isSubmittingReview, setIsSubmittingReview] = useState(false);

    // helper function to find the last completed stage
    const getLastCompletedStage = (pipeline: VideoPipeline): VideoPipelineStage => {
        // define stages in order with their corresponding status fields
        const stagesInOrder: Array<{ stage: VideoPipelineStage; status: VideoPipelineStatus | undefined }> = [
            { stage: VideoPipelineStage.DOCUMENT_PROCESSING, status: pipeline.document_processing_status },
            { stage: VideoPipelineStage.CONTENT_ANALYSIS, status: pipeline.content_analysis_status },
            { stage: VideoPipelineStage.SCRIPT_GENERATION, status: pipeline.script_generation_status },
            { stage: VideoPipelineStage.VIDEO_GENERATION, status: pipeline.video_generation_status },
        ];

        // find the last completed stage
        let lastCompletedStage = VideoPipelineStage.DOCUMENT_PROCESSING;
        for (const { stage, status } of stagesInOrder) {
            if (status === VideoPipelineStatus.COMPLETED) {
                lastCompletedStage = stage;
            }
        }

        return lastCompletedStage;
    };

    const fetchVideoPipeline = async () => {
        setIsLoading(true);
        try {
            const result: VideoPipeline = await client.getVideoPipelineDetails(taskId);
            setVideoPipeline(result);
            setIsProcessingDocument(result.document_processing_status === VideoPipelineStatus.IN_PROGRESS);
            setIsProcessingContent(result.content_analysis_status === VideoPipelineStatus.IN_PROGRESS);
            setIsGeneratingScripts(result.script_generation_status === VideoPipelineStatus.IN_PROGRESS);
            setIsGeneratingVideo(result.video_generation_status === VideoPipelineStatus.IN_PROGRESS);
            // set the selected stage to the last completed stage
            const lastCompletedStage = getLastCompletedStage(result);
            setSelectedStage(lastCompletedStage);
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

    // websocket connection for real-time pipeline updates
    useEffect(() => {
        if (!taskId || !user?.id) {
            return;
        }
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const baseWsUrl = `${baseUrl.replace('http', 'ws').replace('https', 'wss')}`;
        const wsUrl = `${baseWsUrl}/video-pipelines/${taskId}/ws?user_id=${user.id}`;
        const socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            console.log("onopen: connected to pipeline state socket");
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                fetchVideoPipeline();
            } catch (error) {
                console.error("Error parsing WebSocket message:", error);
            }
        };

        socket.onerror = (error) => {
            console.log("onerror: websocket error:", error);
        };

        socket.onclose = () => {
            console.log("onclose: websocket closed");
        };

        // cleanup function to close the websocket connection when the component unmounts
        return () => {
            if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
                socket.close();
            }
        };
    }, [taskId, user?.id]);

    const generateOutlineContent = async (data: CreateVideoOutlineRequest) => {
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
            <div className="flex flex-col md:flex-row gap-6 mx-auto">
                <div className="w-full md:w-1/3 flex flex-col gap-4 order-1 md:order-1">
                    <VideoPipelineStagesManager 
                        videoPipeline={videoPipeline} 
                        onGenerateOutlineContent={generateOutlineContent} 
                        onScriptAndAudioGeneration={scriptAndAudioGeneration} 
                        onVideoGeneration={videoGeneration} 
                        onStageSelect={(stage) => setSelectedStage(stage)}
                        selectedStage={selectedStage}
                        defaultVideoTitle={videoPipeline.name}
                        defaultVideoSubtitle={videoPipeline.instructions}
                        isProcessingContent={isProcessingContent}
                        isGeneratingScripts={isGeneratingScripts}
                        isGeneratingVideo={isGeneratingVideo}
                    />
                </div>
                <div className="w-full md:w-2/3 flex flex-col gap-6 order-2 md:order-2">
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
                                    isProcessingDocument={isProcessingDocument}
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
                                    defaultVideoSubtitle={videoPipeline.instructions}
                                />
                            </CardContent>
                        </Card>
                    )}
                </div>
                <div className="w-full md:w-1/3 flex flex-col gap-4 order-3 md:order-3">
                    <VideoPipelineDetails 
                        name={videoPipeline.name} 
                        instructions={videoPipeline.instructions} 
                        created_at={videoPipeline.created_at}
                        current_stage={videoPipeline.current_stage}
                        status={videoPipeline.status}
                    />
                </div>
            </div>
        </div>
    );
}
