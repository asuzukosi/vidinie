"use client";

import { Image, LineChart, Cpu, Code } from "lucide-react";

interface ParserStageProps {
    rawText?: string;
    imageCount?: number;
}

export function ParserStage({ rawText, imageCount = 4 }: ParserStageProps) {
    const placeholderText = `[Document: Q4_Review.pdf]
[Metadata: PDFProcessor v1.2]

SECTION 1: INTRODUCTION TO PIPELINE
The video generation workflow starts with the ingestion of raw documents...

SECTION 2: TECHNICAL SPECIFICATIONS
MoviePy serves as the core rendering engine. Transitions are calculated based on audio length...

SECTION 3: IMAGE LABELLER OUTPUT
Image ID: IMG_001.jpg | Label: "Technical Architecture Diagram"
Image ID: IMG_002.jpg | Label: "Team Collaboration Workspace"

... [End of Parsing] ...`;

    const imageIcons = [Image, LineChart, Cpu, Code];

    return (
        <div className="space-y-8">
            <div className="max-w-4xl mx-auto">
                <div className="grid grid-cols-2 gap-6">
                    {/* Raw text context */}
                    <div className="space-y-4">
                        <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">
                            Raw Text Context
                        </h3>
                        <div className="bg-zinc-50 dark:bg-zinc-900 p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 text-xs text-zinc-600 dark:text-zinc-400 font-mono leading-relaxed h-[400px] overflow-y-auto">
                            <pre className="whitespace-pre-wrap">{rawText || placeholderText}</pre>
                        </div>
                    </div>

                    {/* Extracted images */}
                    <div className="space-y-4">
                        <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">
                            Extracted Image Assets
                        </h3>
                        <div className="grid grid-cols-2 gap-3">
                            {imageIcons.slice(0, imageCount).map((Icon, index) => (
                                <div
                                    key={index}
                                    className="aspect-video bg-zinc-200 dark:bg-zinc-800 rounded-xl border border-zinc-300 dark:border-zinc-700 flex items-center justify-center"
                                >
                                    <Icon className="w-6 h-6 text-zinc-400" />
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
