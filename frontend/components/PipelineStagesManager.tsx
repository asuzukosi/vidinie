"use client";

import { useState } from "react";
import {
  IconChevronRight,
} from "@tabler/icons-react";
import { PlayIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { CircularProgress } from "@/components/ui/circular-progress";
import { StepIndicator } from "@/components/ui/step-indicator";
import { pipelineProcessingStages } from "@/lib/sdk/constants";
import { PipelineProcessingStage } from "@/lib/sdk/types";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function PipelineStagesManager() {
  const [currentSteps, setCurrentSteps] = useState<PipelineProcessingStage[]>(pipelineProcessingStages);
  const [openStepId, setOpenStepId] = useState<string | null>(() => {
    const firstIncomplete = pipelineProcessingStages.find((s) => !s.completed);
    return firstIncomplete?.id ?? pipelineProcessingStages[0]?.id ?? null;
  });

  const completedCount = currentSteps.filter((s) => s.completed).length;
  const remainingCount = currentSteps.length - completedCount;

  const handleStepClick = (stepId: string) => {
    setOpenStepId(openStepId === stepId ? null : stepId);
  };

  const handleStepAction = (step: PipelineProcessingStage) => {
    setCurrentSteps((prev) =>
      prev.map((s) => (s.id === step.id ? { ...s, completed: true } : s))
    );
  };
  return (
        <div className="rounded-lg border bg-card p-4 text-card-foreground shadow-xs">
          <div className="mb-4 mr-2 flex flex-col justify-between sm:flex-row sm:items-center">
            <h3 className="ml-2 font-semibold text-foreground">
              Create with Vidinie
            </h3>
            <div className="mt-2 flex items-center justify-end sm:mt-0">
              <CircularProgress
                completed={remainingCount}
                total={currentSteps.length}
              />
              <div className="ml-1.5 mr-3 text-sm text-muted-foreground">
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
              const isOpen = openStepId === step.id;
              const isFirst = index === 0;
              const prevStep = currentSteps[index - 1];
              const isPrevOpen = prevStep && openStepId === prevStep.id;

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
                              <div className="flex justify-end mt-auto pt-2">
                                <TooltipProvider>
                                  <div className="flex items-end gap-1">
                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        <Button
                                          variant="outline"
                                          size="icon"
                                          className="h-8 w-8 shadow-md p-2 rounded-md"
                                          onClick={() => handleStepAction(step)}
                                        >
                                          <PlayIcon className="size-4" />
                                        </Button>
                                      </TooltipTrigger>
                                      <TooltipContent side="bottom" align="end">{step.actionLabel}</TooltipContent>
                                    </Tooltip>
                                  </div>
                                </TooltipProvider>
                              </div>
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
  );
}