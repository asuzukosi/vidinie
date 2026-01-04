"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Star } from "lucide-react";
import { VideoPipelineReviewRequest } from "@/lib/sdk/types";

interface ReviewFeedbackModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: VideoPipelineReviewRequest) => void;
  defaultRating?: number;
  defaultFeedback?: string;
}

// default values
const DEFAULT_RATING = 5;
const DEFAULT_FEEDBACK = "";

export function ReviewFeedbackModal({
  open,
  onOpenChange,
  onSubmit,
  defaultRating,
  defaultFeedback = "",
}: ReviewFeedbackModalProps) {
  const [formData, setFormData] = useState<VideoPipelineReviewRequest>({
    rating: defaultRating || DEFAULT_RATING,
    feedback: defaultFeedback || DEFAULT_FEEDBACK,
  });
  const [hoveredRating, setHoveredRating] = useState<number | null>(null);

  const ratingLabels: Record<number, string> = {
    1: "Poor",
    2: "Fair",
    3: "Good",
    4: "Very Good",
    5: "Excellent",
  };

  // reset form when modal opens
  useEffect(() => {
    if (open) {
      setFormData({
        rating: defaultRating || DEFAULT_RATING,
        feedback: defaultFeedback || DEFAULT_FEEDBACK,
      });
      setHoveredRating(null);
    }
  }, [open, defaultRating, defaultFeedback]);

  const handleStarClick = (rating: number) => {
    setFormData({
      ...formData,
      rating,
    });
  };

  const handleStarHover = (rating: number) => {
    setHoveredRating(rating);
  };

  const handleStarLeave = () => {
    setHoveredRating(null);
  };

  const getStarState = (index: number) => {
    const ratingToShow = hoveredRating !== null ? hoveredRating : formData.rating || DEFAULT_RATING;
    return index < ratingToShow;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Review and Feedback</DialogTitle>
          <DialogDescription>
            Share your feedback about the video pipeline. Your rating and comments help us improve.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="py-4">
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="rating">Rating</FieldLabel>
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-3">
                    <div 
                      className="flex items-center gap-1"
                      onMouseLeave={handleStarLeave}
                    >
                      {Array.from({ length: 5 }).map((_, index) => {
                        const starValue = index + 1;
                        const isFilled = getStarState(index);
                        return (
                          <button
                            key={index}
                            type="button"
                            onClick={() => handleStarClick(starValue)}
                            onMouseEnter={() => handleStarHover(starValue)}
                            aria-label={`Rate ${starValue} out of 5`}
                          >
                            <Star
                              className={`size-8 transition-colors cursor-pointer ${
                                isFilled
                                  ? "fill-black text-black"
                                  : "fill-none text-gray-300 hover:text-yellow-300"
                              }`}
                            />
                          </button>
                        );
                      })}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">
                        {formData.rating || DEFAULT_RATING} / 5
                      </span>
                      {hoveredRating && (
                        <span className="text-sm text-muted-foreground">
                          - {ratingLabels[hoveredRating]}
                        </span>
                      )}
                      {!hoveredRating && formData.rating && (
                        <span className="text-sm text-muted-foreground">
                          - {ratingLabels[formData.rating]}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <FieldDescription>
                  Click on the stars to rate your experience (1-5 stars)
                </FieldDescription>
              </Field>

              <Field>
                <FieldLabel htmlFor="feedback">Feedback</FieldLabel>
                <Textarea
                  id="feedback"
                  placeholder="Share your thoughts, suggestions, or any issues you encountered..."
                  value={formData.feedback || ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      feedback: e.target.value,
                    })
                  }
                  rows={5}
                  className="resize-none"
                />
                <FieldDescription>
                  Optional: Provide detailed feedback about the video pipeline
                </FieldDescription>
              </Field>
            </FieldGroup>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit">Submit Review</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

