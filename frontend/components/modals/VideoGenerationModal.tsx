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
import { GenerateVideoPipelineRequest, VideoResolution, BackgroundType } from "@/lib/sdk/types";

interface VideoGenerationModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: GenerateVideoPipelineRequest) => void;
  defaultTitle?: string;
  defaultSubtitle?: string;
}

// Default values defined within the component
const DEFAULT_RESOLUTION = VideoResolution.RESOLUTION_1080P;
const DEFAULT_FPS = 30;
const DEFAULT_TITLE_DURATION = 3.0;
const DEFAULT_END_DURATION = 3.0;
const DEFAULT_TRANSITION_DURATION = 0.5;
const DEFAULT_BACKGROUND_TYPE = BackgroundType.GRADIENT;

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
    background_type: DEFAULT_BACKGROUND_TYPE,
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
        background_type: DEFAULT_BACKGROUND_TYPE,
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
            Configure the settings for video generation. All fields are required.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                value={formData.title}
                onChange={(e) =>
                  setFormData({ ...formData, title: e.target.value })
                }
                placeholder="Enter video title"
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="subtitle">Subtitle / Description</Label>
              <Input
                id="subtitle"
                value={formData.subtitle}
                onChange={(e) =>
                  setFormData({ ...formData, subtitle: e.target.value })
                }
                placeholder="Enter video subtitle or description"
                required
              />
            </div>

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
                  <SelectItem value={VideoResolution.RESOLUTION_4K}>
                    4K
                  </SelectItem>
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
                min="24"
                max="60"
                value={formData.fps}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    fps: parseInt(e.target.value) || 30,
                  })
                }
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="title_duration">Title Duration (seconds)</Label>
              <Input
                id="title_duration"
                type="number"
                step="0.1"
                min="0"
                value={formData.title_duration}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    title_duration: parseFloat(e.target.value) || 0,
                  })
                }
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="end_duration">End Duration (seconds)</Label>
              <Input
                id="end_duration"
                type="number"
                step="0.1"
                min="0"
                value={formData.end_duration}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    end_duration: parseFloat(e.target.value) || 0,
                  })
                }
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="transition_duration">
                Transition Duration (seconds)
              </Label>
              <Input
                id="transition_duration"
                type="number"
                step="0.1"
                min="0"
                value={formData.transition_duration}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    transition_duration: parseFloat(e.target.value) || 0,
                  })
                }
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="background_type">Background Type</Label>
              <Select
                value={formData.background_type}
                onValueChange={(value) =>
                  setFormData({
                    ...formData,
                    background_type: value as BackgroundType,
                  })
                }
              >
                <SelectTrigger id="background_type">
                  <SelectValue placeholder="Select background type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={BackgroundType.GRADIENT}>Gradient</SelectItem>
                  <SelectItem value={BackgroundType.SOLID}>Solid</SelectItem>
                </SelectContent>
              </Select>
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

