"use client";

import React, { useState, useEffect, useRef } from 'react';
import client from '@/lib/sdk/client';

interface VideoPlayerProps {
    videoPipelineId: string;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({ videoPipelineId }) => {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [videoUrl, setVideoUrl] = useState<string>("");

    useEffect(() => {
        const getBaseUrl = async () => {
            const baseUrl = await client.getBaseUrl();
            setVideoUrl(`${baseUrl}/video-pipelines/${videoPipelineId}/output/stream`);
        };
        getBaseUrl();
    }, [videoPipelineId]);

    return (
        <div className="w-full aspect-video rounded-lg border border-zinc-200 dark:border-zinc-800 overflow-hidden">
            {videoUrl ? (
                <video 
                    ref={videoRef}
                    src={videoUrl}
                    controls 
                    className="w-full h-full object-contain"
                />
            ) : (
                <div className="w-full h-full flex items-center justify-center bg-zinc-100 dark:bg-zinc-900">
                    <p className="text-sm text-muted-foreground">Loading video player...</p>
                </div>
            )}
        </div>
    );
}

