"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import {
    PipelineStageNav,
    PipelineFooter,
    pipelineStages,
    ParserStage,
    ContentAnalyserStage,
    NarrationStage,
    FinalExportStage,
} from "@/components/pipeline";

export default function TaskDetailPage() {
    const params = useParams();
    const taskId = params.id as string;

    const [currentStage, setCurrentStage] = useState(1);
    const [progress, setProgress] = useState(0);

    // Simulate progress loading
    useEffect(() => {
        const interval = setInterval(() => {
            setProgress((prev) => (prev >= 100 ? 100 : prev + Math.random() * 5));
        }, 500);
        return () => clearInterval(interval);
    }, []);

    const handlePrev = () => {
        if (currentStage > 1) setCurrentStage(currentStage - 1);
    };

    const handleNext = () => {
        if (currentStage < pipelineStages.length) setCurrentStage(currentStage + 1);
    };

    // Render stage content based on current stage
    const renderStageContent = () => {
        switch (currentStage) {
            case 1:
                return <ParserStage />;
            case 2:
                return <ContentAnalyserStage />;
            case 3:
                return <NarrationStage />;
            case 4:
                return <FinalExportStage />;
            default:
                return null;
        }
    };

    return (
        <div className="flex h-[calc(100vh-2rem)] -m-6 overflow-hidden">
            {/* Sidebar navigation */}
            <PipelineStageNav
                currentStage={currentStage}
                onStageChange={setCurrentStage}
                progress={Math.round(progress)}
            />

            {/* Main content area */}
            <main className="flex-1 flex flex-col bg-white dark:bg-zinc-950 overflow-hidden">
                {/* Stage content */}
                <div className="flex-1 overflow-y-auto p-8">
                    {renderStageContent()}
                </div>

                <PipelineFooter
                    currentStage={currentStage}
                    onPrev={handlePrev}
                    onNext={handleNext}
                />
            </main>
        </div>
    );
}
