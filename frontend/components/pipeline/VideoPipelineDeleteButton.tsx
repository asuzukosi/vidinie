"use client";
import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Loader2, Trash2Icon } from "lucide-react";
import { VideoPipelineTableItem } from "./VideoPipelineTable";
import { toast } from "sonner";

interface VideoPipelineDeleteButtonProps {
  videoPipeline: VideoPipelineTableItem;
  onDelete: (videoPipeline: VideoPipelineTableItem) => void;
}

export function VideoPipelineDeleteButton({
  videoPipeline,
  onDelete,
}: VideoPipelineDeleteButtonProps) {
  const [deletePending, setDeletePending] = useState(false);

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent row click from firing
    setDeletePending(true);
    try {
      onDelete(videoPipeline);
      toast.success("Video pipeline deleted successfully");
    } catch (error) {
      console.error("Delete failed:", error);
      toast.error("Failed to delete video pipeline");
    } finally {
      setDeletePending(false);
    }
  };

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8 text-destructive hover:bg-destructive hover:text-white"
            onClick={handleDelete}
            disabled={deletePending}
          >
            {deletePending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Trash2Icon className="size-4" />
            )}
          </Button>
        </TooltipTrigger>
        <TooltipContent>Delete</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

