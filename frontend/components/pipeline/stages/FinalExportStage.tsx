"use client";

import { Check, Download } from "lucide-react";
import { Button } from "@/components/ui/button";

interface FinalExportStageProps {
    videoDuration?: string;
    onDownload?: () => void;
}

export function FinalExportStage({
    videoDuration = "1-minute",
    onDownload,
    onSaveToCloud,
}: FinalExportStageProps) {
    return (
        <div className="space-y-8">
            <div className="max-w-2xl mx-auto text-center space-y-8 py-12">
                {/* Success icon */}
                <div className="w-20 h-20 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 rounded-full flex items-center justify-center text-3xl mx-auto shadow-lg shadow-emerald-50 dark:shadow-emerald-900/20">
                    <Check className="w-10 h-10" />
                </div>

                {/* Success message */}
                <div>
                    <h2 className="text-2xl font-bold text-zinc-800 dark:text-white">
                        Video Generation Successful
                    </h2>
                    <p className="text-zinc-500 dark:text-zinc-400 text-sm mt-2">
                        Your {videoDuration} video is ready for download and distribution.
                    </p>
                </div>

                {/* Action buttons */}
                <div className="flex flex-col gap-3">
                    <Button
                        onClick={onDownload}
                        className="w-full py-6 flex items-center justify-center gap-3"
                        size="lg"
                    >
                        <Download className="w-5 h-5" />
                        Download Video (MP4)
                    </Button>
                </div>
            </div>
        </div>
    );
}
