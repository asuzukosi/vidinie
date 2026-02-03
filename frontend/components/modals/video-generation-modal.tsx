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
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { GenerateVideoPipelineRequest, VideoResolution } from "@/lib/sdk/types";

interface VideoGenerationModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: GenerateVideoPipelineRequest) => void;
  defaultTitle?: string;
  defaultSubtitle?: string;
}

// Default values defined within the component
const DEFAULT_RESOLUTION = VideoResolution.RESOLUTION_480P;
const DEFAULT_FPS = 15;
const DEFAULT_TITLE_DURATION = 3.0;
const DEFAULT_END_DURATION = 3.0;
const DEFAULT_TRANSITION_DURATION = 0.5;

export function VideoGenerationModal({
  open,
  onOpenChange,
  onSubmit,
  defaultTitle = "",
  defaultSubtitle = "",
}: VideoGenerationModalProps) {
  const [formData, setFormData] = useState<GenerateVideoPipelineRequest>({
    title: defaultTitle,
    subtitle: defaultSubtitle,
    resolution: DEFAULT_RESOLUTION,
    fps: DEFAULT_FPS,
    title_duration: DEFAULT_TITLE_DURATION,
    end_duration: DEFAULT_END_DURATION,
    transition_duration: DEFAULT_TRANSITION_DURATION,
  });

  // reset form when modal opens or title/subtitle change
  useEffect(() => {
    if (open) {
      setFormData({
        title: defaultTitle,
        subtitle: defaultSubtitle,
        resolution: DEFAULT_RESOLUTION,
        fps: DEFAULT_FPS,
        title_duration: DEFAULT_TITLE_DURATION,
        end_duration: DEFAULT_END_DURATION,
        transition_duration: DEFAULT_TRANSITION_DURATION,
      });
    }
  }, [open, defaultTitle, defaultSubtitle]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Video Generation Settings</DialogTitle>
          <DialogDescription>
            Configure the settings for video generation.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="resolution">Resolution</Label>
              <Select
                value={formData.resolution}
                onValueChange={(value) =>
                  setFormData({
                    ...formData,
                    resolution: value as VideoResolution,
                  })
                }
              >
                <SelectTrigger id="resolution">
                  <SelectValue placeholder="Select resolution" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={VideoResolution.RESOLUTION_1080P}>
                    1080P
                  </SelectItem>
                  <SelectItem value={VideoResolution.RESOLUTION_720P}>
                    720P
                  </SelectItem>
                  <SelectItem value={VideoResolution.RESOLUTION_480P}>
                    480P
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="fps">FPS (Frames Per Second)</Label>
              <Input
                id="fps"
                type="number"
                min="10"
                max="30"
                value={formData.fps}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    fps: parseInt(e.target.value),
                  })
                }
                required
              />
            </div>
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

