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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
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

  // reset form when modal opens
  useEffect(() => {
    if (open) {
      setFormData({
        rating: defaultRating || DEFAULT_RATING,
        feedback: defaultFeedback || DEFAULT_FEEDBACK,
      });
    }
  }, [open, defaultRating, defaultFeedback]);

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
                <Select
                  value={String(formData.rating || DEFAULT_RATING)}
                  onValueChange={(value) =>
                    setFormData({
                      ...formData,
                      rating: parseInt(value) || DEFAULT_RATING,
                    })
                  }
                  required
                >
                  <SelectTrigger id="rating">
                    <SelectValue placeholder="Select rating" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1 - Poor</SelectItem>
                    <SelectItem value="2">2 - Fair</SelectItem>
                    <SelectItem value="3">3 - Good</SelectItem>
                    <SelectItem value="4">4 - Very Good</SelectItem>
                    <SelectItem value="5">5 - Excellent</SelectItem>
                  </SelectContent>
                </Select>
                <FieldDescription>
                  Rate your experience with this video pipeline (1-5)
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

