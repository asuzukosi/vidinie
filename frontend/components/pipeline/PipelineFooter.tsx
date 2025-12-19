"use client";

import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { pipelineStages } from "./PipelineStageNav";

interface PipelineFooterProps {
    currentStage: number;
    onPrev: () => void;
    onNext: () => void;
}

export function PipelineFooter({ currentStage, onPrev, onNext }: PipelineFooterProps) {
    const isFirstStage = currentStage === 1;
    const isLastStage = currentStage === pipelineStages.length;
    const nextStage = pipelineStages.find((s) => s.id === currentStage + 1);

    return (
        <footer className="p-6 border-t border-zinc-100 dark:border-zinc-800 flex justify-between items-center bg-white dark:bg-zinc-950 shrink-0">
            <div className="flex gap-4">
                <Button variant="outline" onClick={onPrev} disabled={isFirstStage}>
                    Back
                </Button>
            </div>
            <Button onClick={onNext} className="flex items-center gap-2">
                <span>
                    {isLastStage ? "Finish Pipeline" : `Move to ${nextStage?.title} Stage`}
                </span>
                <ArrowRight className="w-4 h-4" />
            </Button>
        </footer>
    );
}
