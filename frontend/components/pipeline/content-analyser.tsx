"use client";

import { useState } from "react";
import { VideoOutline, ImageSource, CreateVideoOutlineRequest } from "@/lib/sdk/types";
import { Badge } from "@/components/ui/badge";
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from "@/components/ui/accordion";
import Image from "next/image";
import { getLinkToImage } from "@/lib/utils";  
import { Button } from "../ui/button";
import { IconPlus } from "@tabler/icons-react";
import { Loader2 } from "lucide-react";
import { OutlineContentModal } from "@/components/modals/outline-content-modal";

interface ContentAnalyserProps {
    videoOutline?: VideoOutline;
    onGenerateOutlineContent?: (data: CreateVideoOutlineRequest) => void;
    isProcessingContent?: boolean;
}

export function ContentAnalyser({ videoOutline, onGenerateOutlineContent, isProcessingContent = false }: ContentAnalyserProps) {
    const [isOutlineContentModalOpen, setIsOutlineContentModalOpen] = useState(false);

    const handleOutlineContentSubmit = (data: CreateVideoOutlineRequest) => {
        if (onGenerateOutlineContent) {
            onGenerateOutlineContent(data);
        }
        setIsOutlineContentModalOpen(false);
    };

    if (!videoOutline || !videoOutline.segments || videoOutline.segments.length === 0) {
        return (
            <>
                <div className="space-y-8">
                    <div className="max-w-4xl mx-auto space-y-6">
                        <h3 className="font-semibold text-sm">Video Outline Segments</h3>
                        <p className="text-sm text-muted-foreground">No video outline available yet.</p>
                        <Button variant="outline" size="sm"
                            onClick={() => setIsOutlineContentModalOpen(true)}
                            disabled={isProcessingContent}
                            className="w-full flex items-center justify-center gap-2 text-xs border-dashed border-zinc-300 text-zinc-500 hover:text-zinc-700 hover:border-zinc-500">
                            {isProcessingContent ? (
                                <Loader2 className="size-4 animate-spin" />
                            ) : (
                                <IconPlus className="size-4" />
                            )}
                            Generate Video Outline
                        </Button>
                    </div>
                </div>
                <OutlineContentModal
                    open={isOutlineContentModalOpen}
                    onOpenChange={setIsOutlineContentModalOpen}
                    onSubmit={handleOutlineContentSubmit}
                />
            </>
        );
    }

    return (
        <>
            <div className="space-y-8 pt-8">
                <div className="max-w-4xl mx-auto">
                    <div className="space-y-4 mb-4">
                        <div className="flex flex-row justify-between items-center">
                            <h3 className="font-semibold text-sm">Video Outline Segments</h3>
                            <div className="flex flex-row justify-end gap-2 text-xs">
                                <Badge variant="outline">
                                    {videoOutline.total_segments} {videoOutline.total_segments === 1 ? "segment" : "segments"}
                                </Badge>
                                {videoOutline.estimated_duration && (
                                    <Badge variant="outline">
                                        {videoOutline.estimated_duration}s duration
                                    </Badge>
                                )}
                            </div>
                        </div>
                        <Accordion
                            type="single"
                            collapsible
                            className="w-full"
                        >
                            {videoOutline.segments.map((segment, index) => {
                                let imageUrl: string | undefined;
                                let imageType: string | undefined;
                                if (segment.image) {
                                    imageUrl = getLinkToImage(segment.image.path) || undefined;
                                    imageType = segment.image.source === ImageSource.AI_GENERATED ? "AI Generated" : "Source";
                                }
                                return (
                                    <AccordionItem key={index} value={`segment-${index}`}>
                                        <AccordionTrigger className="text-sm flex flex-row justify-between gap-2">
                                            <span>Segment {index + 1}: {segment.title}</span>
                                        </AccordionTrigger>
                                        <AccordionContent className="flex flex-col gap-4">
                                            {imageUrl && (
                                                <div className="relative h-64 rounded-lg overflow-hidden">
                                                    <Image
                                                        src={imageUrl}
                                                        alt={segment.title}
                                                        fill
                                                        className="object-contain"
                                                        unoptimized
                                                    />
                                                </div>
                                            )}
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                                {segment.title && (
                                                    <div>
                                                        <span className="font-medium">Title: </span>
                                                        <span>{segment.title}</span>
                                                    </div>
                                                )}
                                                {segment.purpose && (
                                                    <div>
                                                        <span className="font-medium">Purpose: </span>
                                                        <span>{segment.purpose}</span>
                                                    </div>
                                                )}
                                                {segment.duration && (
                                                    <div>
                                                        <span className="font-medium">Duration: </span>
                                                        <Badge variant="outline">{segment.duration}s</Badge>
                                                    </div>
                                                )}
                                                {segment.word_count && (
                                                    <div>
                                                        <span className="font-medium">Word Count: </span>
                                                        <Badge variant="outline">{segment.word_count}</Badge>
                                                    </div>
                                                )}
                                                {segment.image && segment.image.source && (
                                                    <div>
                                                        <span className="font-medium">Image Type: </span>
                                                        <Badge variant="outline">{imageType}</Badge>
                                                    </div>
                                                )}
                                                {segment.transition_type && (
                                                    <div>
                                                        <span className="font-medium">Transition: </span>
                                                        <Badge variant="outline">{segment.transition_type}</Badge>
                                                    </div>
                                                )}
                                                {segment.key_points && segment.key_points.length > 0 && (
                                                    <div className="md:col-span-2">
                                                        <span className="font-medium">Key Points: </span>
                                                        <div className="flex flex-wrap gap-1 mt-1">
                                                            {segment.key_points.map((point, idx) => (
                                                                <Badge key={idx} variant="secondary">
                                                                    {point}
                                                                </Badge>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                                {segment.visual_keywords && segment.visual_keywords.length > 0 && (
                                                    <div className="md:col-span-2">
                                                        <span className="font-medium">Visual Keywords: </span>
                                                        <div className="flex flex-wrap gap-1 mt-1">
                                                            {segment.visual_keywords.map((keyword, idx) => (
                                                                <Badge key={idx} variant="secondary">
                                                                    {keyword}
                                                                </Badge>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                                {segment.content && (
                                                    <div className="md:col-span-2">
                                                        <span className="font-medium">Content: </span>
                                                        <p className="mt-1 text-muted-foreground whitespace-pre-wrap">{segment.content}</p>
                                                    </div>
                                                )}
                                                {segment.script && (
                                                    <div className="md:col-span-2">
                                                        <span className="font-medium">Script: </span>
                                                        <p className="mt-1 text-muted-foreground italic">"{segment.script}"</p>
                                                    </div>
                                                )}
                                            </div>
                                        </AccordionContent>
                                    </AccordionItem>
                                );
                            })}
                        </Accordion>
                    </div>
                </div>
            </div>
            <OutlineContentModal
                open={isOutlineContentModalOpen}
                onOpenChange={setIsOutlineContentModalOpen}
                onSubmit={handleOutlineContentSubmit}
            />
        </>
    );
}

