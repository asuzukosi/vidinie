import React, { useState, useEffect, useRef } from 'react';

interface VideoPlayerProps {
    pipelineId: string;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({ pipelineId }) => {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [volume, setVolume] = useState(1);

    const videoUrl = `http://localhost:8000/pipelines/stream_video/${pipelineId}`;

    const handleTimeUpdate = () => {
        if (videoRef.current) {
            setCurrentTime(videoRef.current.currentTime);
        }
    };

    const handleLoadedMetadata = () => {
        if (videoRef.current) {
            setDuration(videoRef.current.duration);
        }
    };

    return (
        <div className="max-w-800px h-auto rounded-lg aspect-video border-1 
                        border border-zinc-200 dark:border-zinc-800 shadow-md">
            <video 
                ref={videoRef}
                src={videoUrl}
                onTimeUpdate={handleTimeUpdate}
                onLoadedMetadata={handleLoadedMetadata}
                onPlay={() => setIsPlaying(true)}
                onPause={() => setIsPlaying(false)}
                controls 
                className="w-full h-full object-cover"
            />
        </div>
    )
}