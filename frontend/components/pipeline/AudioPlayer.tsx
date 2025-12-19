"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { Play, Pause } from "lucide-react";

interface AudioPlayerProps {
    filename: string;
    isActive?: boolean;
    audioUrl?: string;
}

export function AudioPlayer({ filename, isActive = false, audioUrl }: AudioPlayerProps) {
    const [isPlaying, setIsPlaying] = useState(false);

    const handlePlayPause = () => {
        setIsPlaying(!isPlaying);
    };

    return (
        <div className="p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl shadow-sm">
            <div className="flex items-center gap-3 mb-2">
                <button
                    onClick={handlePlayPause}
                    className={cn(
                        "w-7 h-7 rounded-full flex items-center justify-center text-[10px] transition-colors",
                        isActive
                            ? "bg-blue-600 text-white hover:bg-blue-700"
                            : "bg-zinc-200 dark:bg-zinc-700 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-300 dark:hover:bg-zinc-600"
                    )}
                >
                    {isPlaying ? (
                        <Pause className="w-3 h-3" />
                    ) : (
                        <Play className="w-3 h-3 ml-0.5" />
                    )}
                </button>
                <div className="text-[11px] font-bold text-zinc-800 dark:text-zinc-200">
                    {filename}
                </div>
            </div>
            {/* Audio waveform visualization */}
            <div
                className={cn(
                    "h-4 w-full rounded",
                    isActive ? "opacity-30" : "opacity-10"
                )}
                style={{
                    background: `repeating-linear-gradient(90deg, #3b82f6 0px, #3b82f6 2px, transparent 2px, transparent 4px)`,
                }}
            />
        </div>
    );
}
