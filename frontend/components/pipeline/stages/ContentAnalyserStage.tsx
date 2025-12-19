"use client";

import { SegmentCard, Segment } from "../SegmentCard";

interface ContentAnalyserStageProps {
    segments?: Segment[];
    totalSegments?: number;
}

const defaultSegments: Segment[] = [
    {
        id: 1,
        title: "Hook",
        script: "The future of video content is here. Let's explore how the VideoGen Pipeline transforms raw documentation into cinematic experiences.",
        imageType: "ai",
    },
    {
        id: 2,
        title: "Problem Statement",
        script: "Manual video editing is slow and costly. Most data stays trapped in text documents that no one reads.",
        imageType: "source",
    },
];

export function ContentAnalyserStage({ segments = defaultSegments, totalSegments = 7 }: ContentAnalyserStageProps) {
    const remainingCount = totalSegments - segments.length;

    return (
        <div className="space-y-8">
            <div className="max-w-4xl mx-auto space-y-6">
                <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">
                    {totalSegments} Pipeline Segments
                </h3>

                {segments.map((segment, index) => (
                    <SegmentCard
                        key={segment.id}
                        segment={segment}
                        isActive={index === 0}
                    />
                ))}

                {remainingCount > 0 && (
                    <div className="text-center py-4 text-[10px] text-zinc-400 font-bold uppercase tracking-widest">
                        + {remainingCount} More Segments Active
                    </div>
                )}
            </div>
        </div>
    );
}
