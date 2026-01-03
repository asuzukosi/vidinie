"use client";

import { useEffect, useMemo, useState } from "react";
import {
  IconChevronRight,
} from "@tabler/icons-react";
import { PlayIcon, Loader2, Lock } from "lucide-react";
import { cn } from "@/lib/utils";
import { CircularProgress } from "@/components/ui/circular-progress";
import { StepIndicator } from "@/components/ui/step-indicator";
import { pipelineProcessingStages } from "@/lib/sdk/constants";
import { VideoPipelineProcessingStage, VideoPipelineStage, VideoPipelineStageStatuses, VideoPipelineStatus, GenerateVideoPipelineRequest, CreateVideoPipelineOutlineRequest, VideoPipelineReviewRequest } from "@/lib/sdk/types";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { toast } from "sonner";
import { VideoGenerationModal } from "@/components/modals/VideoGenerationModal";
import { OutlineContentModal } from "@/components/modals/OutlineContentModal";
import { ReviewFeedbackModal } from "@/components/modals/ReviewFeedbackModal";


interface PipelineStagesManagerProps {
  pipelineStageStatuses: VideoPipelineStageStatuses;
  onGenerateOutlineContent: (data: CreateVideoPipelineOutlineRequest) => void;
  onScriptAndAudioGeneration: () => void;
  onVideoGeneration: (data: GenerateVideoPipelineRequest) => void;
  onReviewAndFeedback: (data: VideoPipelineReviewRequest) => void;
  onStageSelect?: (stage: VideoPipelineStage | null) => void;
  selectedStage?: VideoPipelineStage | null;
  defaultVideoTitle?: string;
  defaultVideoSubtitle?: string;
  isProcessingContent?: boolean;
  isGeneratingScripts?: boolean;
  isGeneratingVideo?: boolean;
  isSubmittingReview?: boolean;
}
export function VideoPipelineStagesManager({ 
  pipelineStageStatuses, 
  onGenerateOutlineContent, 
  onScriptAndAudioGeneration,
  onVideoGeneration,
  onReviewAndFeedback,
  onStageSelect,
  selectedStage: externalSelectedStage,
  defaultVideoTitle = "",
  defaultVideoSubtitle = "",
  isProcessingContent = false,
  isGeneratingScripts = false,
  isGeneratingVideo = false,
  isSubmittingReview = false,
}: PipelineStagesManagerProps) {
  const [currentSteps, setCurrentSteps] = useState<VideoPipelineProcessingStage[]>(pipelineProcessingStages);
  const [internalOpenStepId, setInternalOpenStepId] = useState<VideoPipelineStage | null>(VideoPipelineStage.DOCUMENT_PROCESSING);
  const [completedCount, setCompletedCount] = useState(0);
  const [isVideoGenerationModalOpen, setIsVideoGenerationModalOpen] = useState(false);
  const [isOutlineContentModalOpen, setIsOutlineContentModalOpen] = useState(false);
  const [isReviewFeedbackModalOpen, setIsReviewFeedbackModalOpen] = useState(false);
  
  // use external selectedStage if provided, otherwise use internal state
  const openStepId = externalSelectedStage !== undefined ? externalSelectedStage : internalOpenStepId;

  const updateCurrentSteps = () => {
    const updatedSteps = pipelineProcessingStages.map((stage) => {
      const stageStatus = pipelineStageStatuses[stage.id as VideoPipelineStage];
      const completed = stageStatus === VideoPipelineStatus.COMPLETED;
      return {
        ...stage,
        completed,
      };
    });
    setCurrentSteps(updatedSteps);
    setCompletedCount(updatedSteps.filter((step) => step.completed).length);
  }

  useEffect(() => {
    updateCurrentSteps();
  }, [pipelineStageStatuses]);

  const remainingCount = useMemo(() => {
    return currentSteps.length - completedCount;
  }, [completedCount]);

  const handleStepClick = (stepId: VideoPipelineStage | string) => {
    const stageEnum = stepId as VideoPipelineStage;
    const newSelectedStage = openStepId === stageEnum ? null : stageEnum;
    if (onStageSelect) {
      onStageSelect(newSelectedStage);
    } else {
      setInternalOpenStepId(newSelectedStage);
    }
  }

  const handleStepAction = (step: VideoPipelineProcessingStage) => {
    switch (step.id) {
      case VideoPipelineStage.CONTENT_ANALYSIS:
        setIsOutlineContentModalOpen(true);
        break;
      case VideoPipelineStage.SCRIPT_GENERATION:
        onScriptAndAudioGeneration();
        break;
      case VideoPipelineStage.VIDEO_GENERATION:
        setIsVideoGenerationModalOpen(true);
        break;
      case VideoPipelineStage.REVIEW_AND_FEEDBACK:
        setIsReviewFeedbackModalOpen(true);
        break;
    }
  }

  const handleOutlineContentSubmit = (data: CreateVideoPipelineOutlineRequest) => {
    onGenerateOutlineContent(data);
  }

  const handleVideoGenerationSubmit = (data: GenerateVideoPipelineRequest) => {
    onVideoGeneration(data);
  }

  const handleReviewFeedbackSubmit = (data: VideoPipelineReviewRequest) => {
    onReviewAndFeedback(data);
  }

  const getStageStatus = (stepId: VideoPipelineStage | string): VideoPipelineStatus | null => {
    return pipelineStageStatuses[stepId as VideoPipelineStage] || null;
  }

  const isStageProcessing = (stepId: VideoPipelineStage | string): boolean => {
    const status = getStageStatus(stepId);
    const isStatusInProgress = status === VideoPipelineStatus.IN_PROGRESS;
    
    // Also check if any of the loading states are active for this step
    switch (stepId) {
      case VideoPipelineStage.CONTENT_ANALYSIS:
        return isStatusInProgress || isProcessingContent;
      case VideoPipelineStage.SCRIPT_GENERATION:
        return isStatusInProgress || isGeneratingScripts;
      case VideoPipelineStage.VIDEO_GENERATION:
        return isStatusInProgress || isGeneratingVideo;
      case VideoPipelineStage.REVIEW_AND_FEEDBACK:
        return isSubmittingReview;
      default:
        return isStatusInProgress;
    }
  }


  const isPreviousStepCompleted = (stepIndex: number): boolean => {
    // first step (document_processing) is always available
    if (stepIndex === 0) {
      return true;
    }
    // check if previous step is completed
    const prevStep = currentSteps[stepIndex - 1];
    return prevStep ? prevStep.completed : false;
  }

  const handleLockedStepClick = (step: VideoPipelineProcessingStage, stepIndex: number) => {
    const prevStep = currentSteps[stepIndex - 1];
    if (prevStep) {
      toast.info("Previous step required", {
        description: `Please complete "${prevStep.title}" before running "${step.title}"`,
      });
    }
  }
  return (
    <>
        <div className="rounded-lg border bg-card p-4 text-card-foreground shadow-xs text-sm">
          <div className="mb-4">
            <h3 className="ml-2 font-semibold text-foreground">
              Create with Vidinie
            </h3>
            <div className="mt-2 flex items-center mb-4">
              <CircularProgress
                completed={remainingCount}
                total={currentSteps.length}
              />
              <div className="ml-1.5 mr-3 text-muted-foreground" >
                <span className="font-medium text-foreground">
                  {remainingCount}
                </span>{" "}
                of{" "}
                <span className="font-medium text-foreground">
                  {currentSteps.length} stages
                </span>{" "}
                left
              </div>
            </div>
          </div>
    
          <div className="space-y-0">
            {currentSteps.map((step, index) => {
              const stepStageEnum = step.id as VideoPipelineStage;
              const isOpen = openStepId === stepStageEnum;
              const isFirst = index === 0;
              const prevStep = currentSteps[index - 1];
              const prevStepStageEnum = prevStep ? (prevStep.id as VideoPipelineStage) : null;
              const isPrevOpen = prevStep && openStepId === prevStepStageEnum;
              const showBorderTop = !isFirst && !isOpen && !isPrevOpen;

              return (
                <div
                  key={step.id}
                  className={cn(
                    "group",
                    isOpen && "rounded-lg",
                    showBorderTop && "border-t border-border"
                  )}
                >
                  <div
                    role="button"
                    tabIndex={0}
                    onClick={() => handleStepClick(step.id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        handleStepClick(step.id);
                      }
                    }}
                    className={cn(
                      "block w-full cursor-pointer text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                      isOpen && "rounded-lg"
                    )}
                  >
                    <div
                      className={cn(
                        "relative overflow-hidden rounded-lg transition-colors",
                        isOpen && "border border-border bg-muted"
                      )}
                    >
                      <div className="relative flex items-center justify-between gap-3 py-3 pl-4 pr-2">
                        <div className="flex w-full gap-3">
                          <div className="shrink-0">
                            <StepIndicator completed={step.completed} />
                          </div>
                          <div className="mt-0.5 grow flex flex-col">
                            <h4
                              className={cn(
                                "font-semibold",
                                step.completed
                                  ? "text-primary"
                                  : "text-foreground"
                              )}
                            >
                              {step.title}
                            </h4>
                            <div
                              className={cn(
                                "overflow-hidden transition-all duration-200 flex flex-col",
                                isOpen ? "h-auto opacity-100" : "h-0 opacity-0"
                              )}
                            >
                              <p className="mt-2 text-sm text-muted-foreground sm:max-w-64 md:max-w-xs">
                                {step.description}
                              </p>
                              {!step.completed && (
                              <div className="flex justify-end mt-auto pt-2">
                                <TooltipProvider>
                                  <div className="flex items-end gap-1">
                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        {isPreviousStepCompleted(index) ? (
                                          <Button
                                            variant="outline"
                                            size="icon"
                                            className="h-8 w-8"
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              handleStepAction(step);
                                            }}
                                            disabled={isStageProcessing(step.id)}
                                          >
                                            {isStageProcessing(step.id) ? (
                                              <Loader2 className="size-4 animate-spin" />
                                            ) : (
                                              <PlayIcon className="size-4" />
                                            )}
                                          </Button>
                                        ) : (
                                          <Button
                                            variant="outline"
                                            size="icon"
                                            className="h-8 w-8"
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              handleLockedStepClick(step, index);
                                            }}
                                            disabled
                                          >
                                            <Lock className="size-4" />
                                          </Button>
                                        )}
                                      </TooltipTrigger>
                                      <TooltipContent side="bottom" align="end">
                                        {isStageProcessing(step.id) 
                                          ? "Processing..." 
                                          : isPreviousStepCompleted(index)
                                          ? step.actionLabel
                                          : `Complete the previous step to unlock "${step.title}"`}
                                      </TooltipContent>
                                    </Tooltip>
                                  </div>
                                </TooltipProvider>
                              </div>
                              )}
                            </div>
                          </div>
                        </div>
                        {!isOpen && (
                          <IconChevronRight
                            className="h-4 w-4 shrink-0 text-muted-foreground"
                            aria-hidden="true"
                          />
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        <VideoGenerationModal
          open={isVideoGenerationModalOpen}
          onOpenChange={setIsVideoGenerationModalOpen}
          onSubmit={handleVideoGenerationSubmit}
          defaultTitle={defaultVideoTitle}
          defaultSubtitle={defaultVideoSubtitle}
        />
        <OutlineContentModal
          open={isOutlineContentModalOpen}
          onOpenChange={setIsOutlineContentModalOpen}
          onSubmit={handleOutlineContentSubmit}
        />
        <ReviewFeedbackModal
          open={isReviewFeedbackModalOpen}
          onOpenChange={setIsReviewFeedbackModalOpen}
          onSubmit={handleReviewFeedbackSubmit}
        />
    </>
  );
}