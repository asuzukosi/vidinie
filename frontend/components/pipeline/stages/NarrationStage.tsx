"use client";

import { cn } from "@/lib/utils";
import { AudioPlayer } from "../AudioPlayer";

interface ScriptSegment {
    id: number;
    text: string;
    audioFile: string;
    isActive?: boolean;
}

interface NarrationStageProps {
    scripts?: ScriptSegment[];
}

const defaultScripts: ScriptSegment[] = [
    {
        id: 1,
        text: "The future of video content is here. Let's explore how the VideoGen Pipeline transforms raw documentation into cinematic experiences.",
        audioFile: "S1_Narration_Final.wav",
        isActive: true,
    },
    {
        id: 2,
        text: "Manual video editing is slow and costly. Most data stays trapped in text documents that no one reads.",
        audioFile: "S2_Narration_Draft.wav",
        isActive: false,
    },
];

export function NarrationStage({ scripts = defaultScripts }: NarrationStageProps) {
    return (
        <div className="space-y-8">
            <div className="max-w-4xl mx-auto space-y-6">
                <div className="grid grid-cols-2 gap-6">
                    {/* Script column */}
                    <div className="space-y-4">
                        <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">
                            Full Script Narration
                        </h3>
                        <div className="space-y-4">
                            {scripts.map((segment) => (
                                <div
                                    key={segment.id}
                                    className={cn(
                                        "p-4 bg-zinc-50 dark:bg-zinc-900 rounded-r-xl",
                                        segment.isActive
                                            ? "border-l-4 border-blue-500"
                                            : "border-l-4 border-zinc-200 dark:border-zinc-700"
                                    )}
                                >
                                    <div
                                        className={cn(
                                            "text-[10px] font-bold mb-1",
                                            segment.isActive
                                                ? "text-blue-600 dark:text-blue-400"
                                                : "text-zinc-500 dark:text-zinc-400"
                                        )}
                                    >
                                        SEGMENT {segment.id}
                                    </div>
                                    <p className="text-xs text-zinc-700 dark:text-zinc-300 leading-relaxed">
                                        {segment.text}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Audio column */}
                    <div className="space-y-4">
                        <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">
                            Audio Synthesis
                        </h3>
                        <div className="space-y-4">
                            {scripts.map((segment) => (
                                <AudioPlayer
                                    key={segment.id}
                                    filename={segment.audioFile}
                                    isActive={segment.isActive}
                                />
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
