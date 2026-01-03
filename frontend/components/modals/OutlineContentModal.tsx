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
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { CreateVideoOutlineRequest } from "@/lib/sdk/types";

interface OutlineContentModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: CreateVideoOutlineRequest) => void;
}

// Default values defined within the component
const DEFAULT_SKIP_STOCK = false;
const DEFAULT_TARGET_SEGMENTS = 10;
const DEFAULT_SEGMENT_DURATION = 10;

export function OutlineContentModal({
  open,
  onOpenChange,
  onSubmit,
}: OutlineContentModalProps) {
  const [formData, setFormData] = useState<CreateVideoOutlineRequest>({
    skip_stock: DEFAULT_SKIP_STOCK,
    target_segments: DEFAULT_TARGET_SEGMENTS,
    segment_duration: DEFAULT_SEGMENT_DURATION,
  });

  // reset form when modal opens
  useEffect(() => {
    if (open) {
      setFormData({
        skip_stock: DEFAULT_SKIP_STOCK,
        target_segments: DEFAULT_TARGET_SEGMENTS,
        segment_duration: DEFAULT_SEGMENT_DURATION,
      });
    }
  }, [open]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Content Analysis Settings</DialogTitle>
          <DialogDescription>
            Configure the settings for generating video outline content. All fields are required.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="py-4">
            <FieldGroup>
              <Field orientation="horizontal">
                <Checkbox
                  id="skip_stock"
                  checked={formData.skip_stock}
                  onCheckedChange={(checked) =>
                    setFormData({
                      ...formData,
                      skip_stock: checked === true,
                    })
                  }
                />
                <FieldLabel htmlFor="skip_stock">
                  Skip Stock Images
                </FieldLabel>
              </Field>

              <Field>
                <FieldLabel htmlFor="target_segments">Target Segments</FieldLabel>
                <Input
                  id="target_segments"
                  type="number"
                  min="1"
                  max="50"
                  value={formData.target_segments}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      target_segments: parseInt(e.target.value) || 10,
                    })
                  }
                  required
                />
                <FieldDescription>
                  Number of video segments to generate (1-50)
                </FieldDescription>
              </Field>

              <Field>
                <FieldLabel htmlFor="segment_duration">Segment Duration (seconds)</FieldLabel>
                <Input
                  id="segment_duration"
                  type="number"
                  min="1"
                  max="60"
                  step="1"
                  value={formData.segment_duration}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      segment_duration: parseInt(e.target.value) || 10,
                    })
                  }
                  required
                />
                <FieldDescription>
                  Duration of each segment in seconds (1-60)
                </FieldDescription>
              </Field>
            </FieldGroup>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit">Confirm</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

