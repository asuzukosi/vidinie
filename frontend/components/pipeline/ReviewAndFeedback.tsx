"use client";

import { useState } from "react";
import { VideoPipelineReviewRequest } from "@/lib/sdk/types";
import { Button } from "../ui/button";
import { IconPlus, IconEdit } from "@tabler/icons-react";
import { Loader2, Star } from "lucide-react";
import { ReviewFeedbackModal } from "@/components/modals/ReviewFeedbackModal";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/utils";

interface ReviewAndFeedbackProps {
    rating?: number;
    feedback?: string;
    updated_at?: string;
    onReviewAndFeedback?: (data: VideoPipelineReviewRequest) => void;
    isSubmittingReview?: boolean;
}

export function ReviewAndFeedback({ 
    rating, 
    feedback, 
    updated_at,
    onReviewAndFeedback, 
    isSubmittingReview = false 
}: ReviewAndFeedbackProps) {
    const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);

    const handleReviewSubmit = (data: VideoPipelineReviewRequest) => {
        if (onReviewAndFeedback) {
            onReviewAndFeedback(data);
        }
        setIsReviewModalOpen(false);
    };

    const hasReview = rating !== undefined && rating !== null;

    if (!hasReview) {
        return (
            <>
                <div className="space-y-8 pt-8">
                    <div className="max-w-4xl mx-auto space-y-6">
                        <h3 className="font-semibold text-sm">Review and Feedback</h3>
                        <p className="text-sm text-muted-foreground">No review submitted yet.</p>
                        {onReviewAndFeedback && (
                            <Button variant="outline" size="sm"
                                onClick={() => setIsReviewModalOpen(true)}
                                disabled={isSubmittingReview}
                                className="w-full flex items-center justify-center gap-2 text-xs border-dashed border-zinc-300 text-zinc-500 hover:text-zinc-700 hover:border-zinc-500">
                                {isSubmittingReview ? (
                                    <Loader2 className="size-4 animate-spin" />
                                ) : (
                                    <IconPlus className="size-4" />
                                )}
                                Add Review
                            </Button>
                        )}
                    </div>
                </div>
                <ReviewFeedbackModal
                    open={isReviewModalOpen}
                    onOpenChange={setIsReviewModalOpen}
                    onSubmit={handleReviewSubmit}
                />
            </>
        );
    }

    return (
        <>
            <div className="space-y-8 pt-8">
                <div className="max-w-4xl mx-auto space-y-6">
                    <div className="flex items-center justify-between">
                        <h3 className="font-semibold text-sm">Review and Feedback</h3>
                        {onReviewAndFeedback && (
                            <Button variant="outline" size="sm"
                                onClick={() => setIsReviewModalOpen(true)}
                                disabled={isSubmittingReview}
                                className="flex items-center gap-2">
                                {isSubmittingReview ? (
                                    <Loader2 className="size-4 animate-spin" />
                                ) : (
                                    <IconEdit className="size-4" />
                                )}
                                Edit Review
                            </Button>
                        )}
                    </div>
                    <Card>
                        <CardContent className="pt-6 space-y-4">
                            <div className="flex items-center gap-2">
                                <span className="font-semibold text-sm">Rating:</span>
                                <div className="flex items-center gap-1">
                                    {Array.from({ length: 5 }).map((_, index) => (
                                        <Star
                                            key={index}
                                            className={`size-5 ${
                                                index < rating
                                                    ? "fill-black text-black"
                                                    : "fill-none text-gray-300"
                                            }`}
                                        />
                                    ))}
                                </div>
                                <Badge variant="secondary" className="ml-2">
                                    {rating}/5
                                </Badge>
                            </div>
                            {feedback && (
                                <div className="space-y-2">
                                    <span className="font-semibold text-sm">Feedback:</span>
                                    <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                                        {feedback}
                                    </p>
                                </div>
                            )}
                            {updated_at && (
                                <div className="text-xs text-muted-foreground">
                                    Last updated: {formatDate(updated_at)}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>
            <ReviewFeedbackModal
                open={isReviewModalOpen}
                onOpenChange={setIsReviewModalOpen}
                onSubmit={handleReviewSubmit}
                defaultRating={rating}
                defaultFeedback={feedback}
            />
        </>
    );
}

