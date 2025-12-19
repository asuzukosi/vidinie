"use client";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Bot } from "lucide-react";

export interface Segment {
    id: number;
    title: string;
    script: string;
    imageType: "ai" | "source";
    imageUrl?: string;
}

interface SegmentCardProps {
    segment: Segment;
    isActive?: boolean;
    onEditScript?: () => void;
    onChangeVisual?: () => void;
}

export function SegmentCard({ segment, isActive = true, onEditScript, onChangeVisual }: SegmentCardProps) {
    return (
        <div
            className={cn(
                "bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl overflow-hidden shadow-sm",
                !isActive && "opacity-80"
            )}
        >
            <div className="bg-zinc-50 dark:bg-zinc-800/50 px-5 py-3 border-b border-zinc-200 dark:border-zinc-700 flex justify-between items-center">
                <span className="text-xs font-bold text-zinc-800 dark:text-zinc-200">
                    Segment {segment.id}: {segment.title}
                </span>
                <Badge
                    variant="outline"
                    className={cn(
                        "text-[10px] font-bold border-0",
                        segment.imageType === "ai"
                            ? "bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400"
                            : "bg-zinc-200 text-zinc-600 dark:bg-zinc-700 dark:text-zinc-400"
                    )}
                >
                    {segment.imageType === "ai" ? "Image Labeled" : "Source Image"}
                </Badge>
            </div>
            <div className="p-6 flex gap-6">
                <div className="w-48 h-28 bg-zinc-100 dark:bg-zinc-800 rounded-xl border border-zinc-200 dark:border-zinc-700 flex items-center justify-center relative group">
                    {segment.imageUrl ? (
                        <video
                            src={segment.imageUrl}
                            className="w-full h-full object-cover rounded-xl"
                        />
                    ) : (
                        <Bot className="w-6 h-6 text-zinc-300 dark:text-zinc-600 group-hover:scale-110 transition-transform" />
                    )}
                    {segment.imageType === "ai" && (
                        <span className="absolute bottom-2 right-2 text-[9px] bg-white dark:bg-zinc-800 px-2 py-0.5 rounded shadow text-zinc-500 dark:text-zinc-400">
                            AI Generated
                        </span>
                    )}
                </div>
                <div className="flex-1">
                    <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed italic">
                        "{segment.script}"
                    </p>
                    {isActive && (
                        <div className="mt-4 flex gap-4">
                            <button
                                onClick={onEditScript}
                                className="text-[10px] font-bold text-blue-600 hover:underline"
                            >
                                Edit Script
                            </button>
                            <button
                                onClick={onChangeVisual}
                                className="text-[10px] font-bold text-blue-600 hover:underline"
                            >
                                Change Visual
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
