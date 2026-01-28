"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { VideoPlayer } from "@/components/utils/video-player";
import { GenerateVideoPipelineRequest, VideoPipelineReviewRequest } from "@/lib/sdk/types";
import { Button } from "@/components/ui/button";
import { IconPlus, IconDownload } from "@tabler/icons-react";
import { Loader2 } from "lucide-react";
import { VideoGenerationModal } from "@/components/modals/video-generation-modal";
import { ReviewAndFeedback } from "@/components/pipeline/review-and-feedback";
import client from "@/lib/sdk/client";
import { toast } from "sonner";
import { useAppSelector } from "@/lib/store/hooks";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { event } from "@/lib/gtag";

interface VideoGenerationProps {
    videoPipelineId: string;
    videoPath?: string;
    rating?: number;
    feedback?: string;
    updated_at?: string;
    onVideoGeneration?: (data: GenerateVideoPipelineRequest) => void;
    onReviewAndFeedback?: (data: VideoPipelineReviewRequest) => void;
    isGeneratingVideo?: boolean;
    isSubmittingReview?: boolean;
    defaultVideoTitle?: string;
    defaultVideoSubtitle?: string;
}

export function VideoGeneration({ 
    videoPipelineId,
    videoPath,
    rating,
    feedback,
    updated_at,
    onVideoGeneration,
    onReviewAndFeedback,
    isGeneratingVideo = false,
    isSubmittingReview = false,
    defaultVideoTitle = "",
    defaultVideoSubtitle = ""
}: VideoGenerationProps) {
    const router = useRouter();
    const user = useAppSelector((state) => state.auth.user);
    const subscription = user?.current_subscription || "free";
    const [isVideoGenerationModalOpen, setIsVideoGenerationModalOpen] = useState(false);
    const [isDownloading, setIsDownloading] = useState(false);
    const [isUpgradeModalOpen, setIsUpgradeModalOpen] = useState(false);

    const handleVideoGenerationSubmit = (data: GenerateVideoPipelineRequest) => {
        if (onVideoGeneration) {
            onVideoGeneration(data);
        }
        setIsVideoGenerationModalOpen(false);
    };

    const handleDownload = async () => {
        // check if user has free subscription
        if (subscription === "free") {
            setIsUpgradeModalOpen(true);
            return;
        }
        event({
            action: "video_download_requested_with_free_subscription",
            category: "video_pipeline",
            label: user?.email || "unknown",
            value: 1,
        });
        setIsDownloading(true);
        event({
            action: "video_download_started",
            category: "video_pipeline",
            label: user?.email || "unknown",
            value: 1,
        });
        try {
            const blob = await client.downloadVideoPipelineOutput(videoPipelineId);
            // Create a blob URL and trigger download
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `video-${videoPipelineId}.mp4`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            toast.success("Video downloaded successfully");
        } catch (error: any) {
            console.error("Error downloading video:", error);
            toast.error(error.message || "Failed to download video");
        } finally {
            setIsDownloading(false);
            event({
                action: "video_download_completed",
                category: "video_pipeline",
                label: user?.email || "unknown",
                value: 1,
            });
        }
    };

    const handleUpgrade = () => {
        setIsUpgradeModalOpen(false);
        router.push("/settings");
    };

    if (!videoPath) {
        return (
            <>
                <div className="space-y-8 pt-8">
                    <div className="max-w-4xl mx-auto space-y-6">
                        <h3 className="font-semibold text-sm">Generated Video</h3>
                        <p className="text-sm text-muted-foreground">No video available yet.</p>
                        {onVideoGeneration && (
                            <Button variant="outline" size="sm"
                                onClick={() => setIsVideoGenerationModalOpen(true)}
                                disabled={isGeneratingVideo}
                                className="w-full flex items-center justify-center gap-2 text-xs border-dashed border-zinc-300 text-zinc-500 hover:text-zinc-700 hover:border-zinc-500">
                                {isGeneratingVideo ? (
                                    <Loader2 className="size-4 animate-spin" />
                                ) : (
                                    <IconPlus className="size-4" />
                                )}
                                Generate Video
                            </Button>
                        )}
                    </div>
                </div>
                <VideoGenerationModal
                    open={isVideoGenerationModalOpen}
                    onOpenChange={setIsVideoGenerationModalOpen}
                    onSubmit={handleVideoGenerationSubmit}
                    defaultTitle={defaultVideoTitle}
                    defaultSubtitle={defaultVideoSubtitle}
                />
            </>
        );
    }

    return (
        <>
            <div className="space-y-8 pt-8">
                <div className="max-w-4xl mx-auto space-y-6">
                    <div className="space-y-4">
                        <h3 className="font-semibold text-sm">Generated Video</h3>
                        <VideoPlayer videoPipelineId={videoPipelineId} />
                        <div className="flex justify-end">
                            <Button
                                variant="secondary"
                                size="sm"
                                onClick={handleDownload}
                                disabled={isDownloading}
                                className="flex items-center gap-2"
                            >
                                {isDownloading ? (
                                    <Loader2 className="size-4 animate-spin" />
                                ) : (
                                    <IconDownload className="size-4" />
                                )}
                                {isDownloading ? "Downloading..." : "Download"}
                            </Button>
                        </div>
                    </div>
                    {videoPath && (
                        <div className="pt-6 border-t">
                            <ReviewAndFeedback 
                                rating={rating}
                                feedback={feedback}
                                updated_at={updated_at}
                                onReviewAndFeedback={onReviewAndFeedback}
                                isSubmittingReview={isSubmittingReview}
                            />
                        </div>
                    )}
                </div>
            </div>
            <Dialog open={isUpgradeModalOpen} onOpenChange={setIsUpgradeModalOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Upgrade Required</DialogTitle>
                        <DialogDescription>
                            Video downloads are only available for Starter and Professional subscription plans. 
                            Upgrade your subscription to download your videos.
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setIsUpgradeModalOpen(false)}>
                            Cancel
                        </Button>
                        <Button onClick={handleUpgrade}>
                            Upgrade Subscription
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </>
    );
}

