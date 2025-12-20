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

    const videoUrl = `http://localhost:8000/api/pipelines/stream_video/${pipelineId}`;
    const togglePlayPause = () => {
        if (videoRef.current) {
            if (isPlaying) {
                videoRef.current.pause();
            } else {
                videoRef.current.play();
            }
            setIsPlaying(!isPlaying);
        }
    };

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

    const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
        const time = parseFloat(e.target.value);
        if (videoRef.current) {
            videoRef.current.currentTime = time;
            setCurrentTime(time);
        }
    };

    const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const volume = parseFloat(e.target.value);
        if (videoRef.current) {
            videoRef.current.volume = volume;
            setVolume(volume);
        }
    };
    const formatTime = (seconds: number): string => {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    };
    return (
        <div className="max-w-800px mx-auto">
            <video 
                ref={videoRef}
                src={videoUrl}
                onTimeUpdate={handleTimeUpdate}
                onLoadedMetadata={handleLoadedMetadata}
                onPlay={() => setIsPlaying(true)}
                onPause={() => setIsPlaying(false)}
                controls 
                style={{ width: '100%', height: 'auto', maxWidth: '800px'}} />
            <div className="flex items-center gap-10, p-10 rounded-md bg-gray-100">
                <button onClick={togglePlayPause} className="bg-blue-500 text-white px-4 py-2 rounded-md mt-4 hover:bg-blue-600">
                    {isPlaying ? 'Pause' : 'Play'}
                </button>
                <span>{formatTime(currentTime)} / {formatTime(duration)}</span>
        
                <input
                    type="range"
                    min="0"
                    max={duration}
                    value={currentTime}
                    onChange={handleSeek}
                    style={{ flex: 1, margin: '0 10px' }}
                />
        
                <label>
                volume
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.01"
                        value={volume}
                        onChange={handleVolumeChange}
                        style={{ width: '80px' }}
                    />
                </label>
            </div>
        </div>
    )
}