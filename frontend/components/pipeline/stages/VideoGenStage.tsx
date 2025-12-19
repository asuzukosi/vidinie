"use client";

import { Film, SlidersHorizontal, Music, Loader2 } from "lucide-react";

interface VideoGenStageProps {
    progress?: number;
    currentSegment?: number;
    totalDuration?: string;
    currentTime?: string;
    videoUrl?: string;
}

export function VideoGenStage({
    progress = 65,
    currentSegment = 3,
    totalDuration = "01:05",
    currentTime = "00:14",
    videoUrl,
}: VideoGenStageProps) {
    return (
        <div className="space-y-8">
            <div className="max-w-4xl mx-auto">
                {/* Video preview */}
                <div className="bg-zinc-900 aspect-video rounded-3xl shadow-2xl relative overflow-hidden flex items-center justify-center group">
                    {videoUrl ? (
                        <video
                            src={videoUrl}
                            className="w-full h-full object-cover"
                            controls
                        />
                    ) : (
                        <div className="text-center space-y-4">
                            <div className="inline-flex items-center gap-3 px-4 py-2 bg-white/10 backdrop-blur-md border border-white/20 rounded-full text-white text-xs">
                                <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                                Rendering Sequence... {progress}%
                            </div>
                            <p className="text-white/40 text-[10px] uppercase tracking-widest font-bold">
                                Rendering Engine Processing
                            </p>
                        </div>
                    )}

                    {/* Progress overlay */}
                    <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-black/80 to-transparent">
                        <div className="flex items-center justify-between text-white text-[10px] mb-2 font-bold">
                            <span>{currentTime} / {totalDuration}</span>
                            <span>Segment {currentSegment}: Transitioning...</span>
                        </div>
                        <div className="w-full bg-white/20 h-1 rounded-full overflow-hidden">
                            <div
                                className="bg-blue-500 h-1 transition-all duration-300"
                                style={{ width: `${(parseInt(currentTime.split(":")[1]) / parseInt(totalDuration.split(":")[1])) * 100}%` }}
                            />
                        </div>
                    </div>
                </div>

                {/* Render options */}
                <div className="mt-10 grid grid-cols-3 gap-6">
                    <div className="p-4 border border-zinc-200 dark:border-zinc-800 rounded-2xl bg-white dark:bg-zinc-900">
                        <Film className="w-5 h-5 text-blue-500 mb-2" />
                        <div className="text-xs font-bold text-zinc-800 dark:text-zinc-200">
                            Concatenate
                        </div>
                        <div className="text-[10px] text-zinc-400">
                            Joining 7 clips
                        </div>
                    </div>
                    <div className="p-4 border border-zinc-200 dark:border-zinc-800 rounded-2xl bg-white dark:bg-zinc-900">
                        <SlidersHorizontal className="w-5 h-5 text-indigo-500 mb-2" />
                        <div className="text-xs font-bold text-zinc-800 dark:text-zinc-200">
                            Transitions
                        </div>
                        <div className="text-[10px] text-zinc-400">
                            Cross-fade 0.5s
                        </div>
                    </div>
                    <div className="p-4 border border-zinc-200 dark:border-zinc-800 rounded-2xl bg-white dark:bg-zinc-900">
                        <Music className="w-5 h-5 text-emerald-500 mb-2" />
                        <div className="text-xs font-bold text-zinc-800 dark:text-zinc-200">
                            Audio Overlay
                        </div>
                        <div className="text-[10px] text-zinc-400">
                            Background music 5%
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
