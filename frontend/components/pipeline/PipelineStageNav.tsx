"use client";

import { cn } from "@/lib/utils";
import {
  IconChevronRight,
  IconCircleCheckFilled,
  IconCircleDashed,
} from "@tabler/icons-react";
import { CheckCheck, FileCode, Mic, SearchCheck } from "lucide-react";

export interface PipelineStage {
  id: number;
  title: string;
  subtitle: string;
  icon: React.ElementType;
}

export const pipelineStages: PipelineStage[] = [
  { id: 1, title: "Parser", subtitle: "Data Extraction", icon: FileCode },
  {
    id: 2,
    title: "Content Analyser",
    subtitle: "7 Segment Logic",
    icon: SearchCheck,
  },
  { id: 3, title: "Narration", subtitle: "Script & Audio", icon: Mic },
  {
    id: 4,
    title: "Final Export",
    subtitle: "Review & Download",
    icon: CheckCheck,
  },
];

interface PipelineStageNavProps {
  currentStage: number;
  onStageChange: (stageId: number) => void;
  progress?: number;
}

function CircularProgress({
  remaining,
  total,
}: {
  remaining: number;
  total: number;
}) {
  const progress = total > 0 ? ((total - remaining) / total) * 100 : 0;
  const strokeDashoffset = 100 - progress;

  return (
    <svg
      className="-rotate-90 scale-y-[-1]"
      height="14"
      width="14"
      viewBox="0 0 14 14"
    >
      <circle
        className="stroke-muted"
        cx="7"
        cy="7"
        fill="none"
        r="6"
        strokeWidth="2"
        pathLength="100"
      />
      <circle
        className="stroke-primary"
        cx="7"
        cy="7"
        fill="none"
        r="6"
        strokeWidth="2"
        pathLength="100"
        strokeDasharray="100"
        strokeLinecap="round"
        style={{ strokeDashoffset }}
      />
    </svg>
  );
}

function StepIndicator({ completed }: { completed: boolean }) {
  if (completed) {
    return (
      <IconCircleCheckFilled
        className="mt-1 size-4.5 shrink-0 text-primary"
        aria-hidden="true"
      />
    );
  }
  return (
    <IconCircleDashed
      className="mt-1 size-5 shrink-0 stroke-muted-foreground/40"
      strokeWidth={2}
      aria-hidden="true"
    />
  );
}

export function PipelineStageNav({
  currentStage,
  onStageChange,
  progress = 0,
}: PipelineStageNavProps) {
  const completedCount = Math.max(0, currentStage - 1);
  const remainingCount = pipelineStages.length - completedCount;
  const safeProgress = Math.min(100, Math.max(0, progress));

  return (
    <aside className="w-72 border-r border-zinc-200 bg-zinc-50/50 dark:border-zinc-800 dark:bg-zinc-900/50 flex flex-col shrink-0 md:ml-4">
      <div className="p-4 flex-1 overflow-y-auto">
        <div className="rounded-lg border bg-card p-4 text-card-foreground shadow-xs">
          <div className="mb-4 flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-foreground">
                Workflow stages
              </h3>
              <div className="flex items-center">
                <CircularProgress
                  remaining={remainingCount}
                  total={pipelineStages.length}
                />
                <div className="ml-1.5 text-xs text-muted-foreground">
                  <span className="font-medium text-foreground">
                    {remainingCount}
                  </span>{" "}
                  of{" "}
                  <span className="font-medium text-foreground">
                    {pipelineStages.length}
                  </span>{" "}
                  stages left
                </div>
              </div>
            </div>
            <div className="rounded-md border bg-muted/40 px-3 py-2">
              <div className="flex items-center justify-between text-[10px] font-semibold text-muted-foreground">
                <span>Processing</span>
                <span className="text-foreground">{safeProgress}%</span>
              </div>
              <div className="mt-1 h-1 w-full rounded-full bg-muted">
                <div
                  className="h-1 rounded-full bg-primary transition-all duration-300"
                  style={{ width: `${safeProgress}%` }}
                />
              </div>
            </div>
          </div>

          <div className="space-y-0">
            {pipelineStages.map((stage, index) => {
              const isOpen = currentStage === stage.id;
              const isCompleted = stage.id < currentStage;
              const isFirst = index === 0;
              const prevStage = pipelineStages[index - 1];
              const isPrevOpen =
                prevStage && currentStage === prevStage.id;
              const showBorderTop = !isFirst && !isOpen && !isPrevOpen;

              return (
                <div
                  key={stage.id}
                  className={cn(
                    "group",
                    isOpen && "rounded-lg",
                    showBorderTop && "border-t border-border"
                  )}
                >
                  <div
                    role="button"
                    tabIndex={0}
                    onClick={() => onStageChange(stage.id)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        onStageChange(stage.id);
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
                            <StepIndicator completed={isCompleted} />
                          </div>
                          <div className="mt-0.5 grow">
                            <h4
                              className={cn(
                                "font-semibold",
                                isCompleted ? "text-primary" : "text-foreground"
                              )}
                            >
                              {stage.title}
                            </h4>
                            <div
                              className={cn(
                                "overflow-hidden transition-all duration-200",
                                isOpen ? "h-auto opacity-100" : "h-0 opacity-0"
                              )}
                            >
                              <p className="mt-2 text-sm text-muted-foreground">
                                {stage.subtitle}
                              </p>
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
      </div>
    </aside>
  );
}
