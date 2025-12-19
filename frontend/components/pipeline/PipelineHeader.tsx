"use client";

import Link from "next/link";
import { ArrowLeft, Settings } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface PipelineHeaderProps {
    title: string;
    status?: "live" | "processing" | "complete";
    onStartRender?: () => void;
}

export function PipelineHeader({ title, status = "live", onStartRender }: PipelineHeaderProps) {
    const statusConfig = {
        live: { label: "Live Pipeline", className: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400" },
        processing: { label: "Processing", className: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400" },
        complete: { label: "Complete", className: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" },
    };

    return (
        <header className="h-16 border-b border-zinc-100 dark:border-zinc-800 grid grid-cols-[1fr_auto] items-center px-4 shrink-0 bg-white dark:bg-zinc-950">
            <div className="flex items-center gap-3 overflow-hidden">
                <Link
                    href="/tasks"
                    className="flex items-center justify-center w-8 h-8 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors flex-shrink-0"
                >
                    <ArrowLeft className="w-4 h-4 text-zinc-600 dark:text-zinc-400" />
                </Link>
                <h1 className="font-bold text-zinc-800 dark:text-white truncate">{title}</h1>
                <Badge
                    variant="outline"
                    className={`text-[10px] font-bold border-0 flex-shrink-0 hidden sm:inline-flex ${statusConfig[status].className}`}
                >
                    {statusConfig[status].label}
                </Badge>
            </div>
            <div className="flex items-center gap-3 pl-4">
                <button className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors">
                    <Settings className="w-5 h-5" />
                </button>
                <Button onClick={onStartRender} size="sm">
                    Start Render
                </Button>
            </div>
        </header>
    );
}
