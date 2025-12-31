"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import {
    // PipelineStageNav,
    // PipelineFooter,
    // pipelineStages,
    DocumentProcessing,
    // ContentAnalyserStage,
    // NarrationStage,
    // FinalExportStage,
    // PipelineStage,
} from "@/components/pipeline";
import client from "@/lib/sdk/client";
import { PipelineData, PipelineStageStatisticsManager } from "@/lib/sdk/types";
import { LoadingPage } from "@/components/LoadingPage";
import { PipelineStagesManager } from "@/components/PipelineStagesManager";
import { PipelineTaskDetails } from "@/components/PipelineTaskDetails";

export default function TaskDetailPage() {
    const params = useParams();
    const taskId = params.id as string;
    const [taskDetails, setTaskDetails] = useState<PipelineData | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const fetchTaskDetails = async () => {
        setIsLoading(true);
        const result: PipelineData = await client.getPipelineDetails(taskId);
        setTaskDetails(result);
        setIsLoading(false);
    };

    useEffect(() => {
        fetchTaskDetails().catch(console.error);
    }, [taskId]);

    return (
        <div className="p-4">
            {isLoading ? (
                <LoadingPage />
            ) : (
                <div className="flex flex-row gap-4 mx-auto">
                    <div className="w-1/3 flex flex-col gap-4">
                        <PipelineStagesManager pipelineStageStatistics={taskDetails?.stage_statistics as PipelineStageStatisticsManager} />
                        <PipelineTaskDetails name={taskDetails?.name || ""} description={taskDetails?.description || ""} tags={taskDetails?.tags || []} projects={taskDetails?.projects || []} />
                    </div>
                    <div className="w-2/3">
                        <div className="text-sm whitespace-pre-wrap break-words max-w-full" style={{ wordBreak: "break-word" }}>
                            <DocumentProcessing content={taskDetails?.parsed_content} images={taskDetails?.images_metadata} />
                            
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
