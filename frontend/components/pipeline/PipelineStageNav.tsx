"use client";

import { cn } from "@/lib/utils";
import {
    FileCode,
    SearchCheck,
    Mic,
    Clapperboard,
    CheckCheck,
} from "lucide-react";

export interface PipelineStage {
    id: number;
    title: string;
    subtitle: string;
    icon: React.ElementType;
}

export const pipelineStages: PipelineStage[] = [
    { id: 1, title: "Parser", subtitle: "Data Extraction", icon: FileCode },
    { id: 2, title: "Content Analyser", subtitle: "7 Segment Logic", icon: SearchCheck },
    { id: 3, title: "Narration", subtitle: "Script & Audio", icon: Mic },
    { id: 4, title: "Final Export", subtitle: "Review & Download", icon: CheckCheck },
];

interface PipelineStageNavProps {
    currentStage: number;
    onStageChange: (stageId: number) => void;
    progress?: number;
}

export function PipelineStageNav({ currentStage, onStageChange, progress = 0 }: PipelineStageNavProps) {
    return (
        <aside className="w-72 border-r border-zinc-200 bg-zinc-50/50 dark:border-zinc-800 dark:bg-zinc-900/50 flex flex-col shrink-0">
            <div className="p-6 flex-1 overflow-y-auto">
                <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-6">
                    Workflow Stages
                </h3>
                <nav className="space-y-3">
                    {pipelineStages.map((stage) => {
                        const isActive = currentStage === stage.id;
                        const Icon = stage.icon;

                        return (
                            <button
                                key={stage.id}
                                onClick={() => onStageChange(stage.id)}
                                className={cn(
                                    "w-full flex items-center gap-3 p-3 rounded-xl transition-all text-left",
                                    isActive
                                        ? "border-2 border-blue-600 bg-blue-50 dark:bg-blue-950/30"
                                        : "bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 hover:border-blue-300 dark:hover:border-blue-700"
                                )}
                            >
                                <div
                                    className={cn(
                                        "w-8 h-8 rounded-lg flex items-center justify-center",
                                        isActive
                                            ? "bg-blue-600"
                                            : "bg-zinc-100 dark:bg-zinc-800"
                                    )}
                                >
                                    <Icon
                                        className={cn(
                                            "w-4 h-4",
                                            isActive ? "text-white" : "text-zinc-400"
                                        )}
                                    />
                                </div>
                                <div>
                                    <div
                                        className={cn(
                                            "text-[11px] font-bold",
                                            isActive ? "text-blue-700 dark:text-blue-400" : "text-zinc-800 dark:text-zinc-200"
                                        )}
                                    >
                                        {stage.title}
                                    </div>
                                    <div
                                        className={cn(
                                            "text-[9px]",
                                            isActive ? "text-blue-600/70 dark:text-blue-400/70" : "text-zinc-400"
                                        )}
                                    >
                                        {stage.subtitle}
                                    </div>
                                </div>
                            </button>
                        );
                    })}
                </nav>
            </div>

            {/* Progress indicator */}
            <div className="p-6 border-t border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
                <div className="p-4 bg-zinc-50 dark:bg-zinc-800/50 rounded-xl border border-zinc-100 dark:border-zinc-700">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-bold text-zinc-500 dark:text-zinc-400">
                            Processing Load
                        </span>
                        <span className="text-[10px] font-bold text-blue-600">
                            {progress}%
                        </span>
                    </div>
                    <div className="w-full bg-zinc-200 dark:bg-zinc-700 rounded-full h-1">
                        <div
                            className="bg-blue-600 h-1 rounded-full transition-all duration-300"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                </div>
            </div>
        </aside>
    );
}
