"use client";

import { VideoPipelineScript } from "@/lib/sdk/types";
import { Badge } from "@/components/ui/badge";
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from "@/components/ui/accordion";
import { getLinkToImage } from "@/lib/utils";
import { Button } from "../ui/button";
import { IconPlus } from "@tabler/icons-react";
import { Loader2 } from "lucide-react";

interface ScriptAndVoiceoversProps {
    scriptData?: VideoPipelineScript;
    fullAudioPath?: string;
    fullAudioDuration?: number;
    onScriptAndAudioGeneration?: () => void;
    isGeneratingScripts?: boolean;
}

export function ScriptAndVoiceovers({ 
    scriptData, 
    fullAudioPath, 
    fullAudioDuration,
    onScriptAndAudioGeneration,
    isGeneratingScripts = false
}: ScriptAndVoiceoversProps) {
    if (!scriptData || !scriptData.segments || scriptData.segments.length === 0) {
        return (
            <div className="space-y-8 pt-8">
                <div className="max-w-4xl mx-auto space-y-6">
                    <h3 className="font-semibold text-sm">Script and Voiceovers</h3>
                    <p className="text-sm text-muted-foreground">No script data available yet.</p>
                    {onScriptAndAudioGeneration && (
                        <Button variant="outline" size="sm"
                            onClick={onScriptAndAudioGeneration}
                            disabled={isGeneratingScripts}
                            className="w-full flex items-center justify-center gap-2 text-xs border-dashed border-zinc-300 text-zinc-500 hover:text-zinc-700 hover:border-zinc-500">
                            {isGeneratingScripts ? (
                                <Loader2 className="size-4 animate-spin" />
                            ) : (
                                <IconPlus className="size-4" />
                            )}
                            Generate Scripts and Voiceovers
                        </Button>
                    )}
                </div>
            </div>
        );
    }

    const fullAudioUrl = getLinkToImage(fullAudioPath) || undefined;

    return (
        <div className="space-y-8 pt-8">
            <div className="max-w-4xl mx-auto">
                <div className="space-y-4 mb-4">
                    <div className="flex flex-row justify-between items-center">
                        <h3 className="font-semibold text-sm">Script and Voiceovers</h3>
                        <div className="flex flex-row justify-end gap-2 text-xs">
                            <Badge variant="outline">
                                {scriptData.total_segments} {scriptData.total_segments === 1 ? "segment" : "segments"}
                            </Badge>
                            {fullAudioDuration && (
                                <Badge variant="outline">
                                    {fullAudioDuration}s total duration
                                </Badge>
                            )}
                        </div>
                    </div>

                    {/* Full Audio Player */}
                    {fullAudioUrl && (
                        <div className="mb-4">
                            <h4 className="font-semibold text-sm mb-2">Full Audio</h4>
                                <audio controls className="w-full" src={fullAudioUrl}>
                                    Your browser does not support the audio element.
                                </audio>
                        </div>
                    )}

                    {/* Full Script Text */}
                    {scriptData.full_script && (
                        <div className="space-y-4 mb-4">
                            <Accordion
                                type="single"
                                collapsible
                                className="w-full"
                            >
                                <AccordionItem value="full-script">
                                    <AccordionTrigger className="text-sm">
                                        <span>Full Script</span>
                                    </AccordionTrigger>
                                    <AccordionContent className="flex flex-col gap-4">
                                        <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap italic">
                                            "{scriptData.full_script}"
                                        </p>
                                    </AccordionContent>
                                </AccordionItem>
                            </Accordion>
                        </div>
                    )}

                    {/* Segments Accordion */}
                    <div className="space-y-4 mb-4">
                        <h3 className="font-semibold text-sm">Segments</h3>
                        <Accordion
                            type="single"
                            collapsible
                            className="w-full"
                        >
                            {scriptData.segments.map((segment, index) => {
                                const audioUrl = getLinkToImage(segment.audio_file) || undefined;
                                return (
                                    <AccordionItem key={index} value={`segment-${index}`}>
                                        <AccordionTrigger className="text-sm flex flex-row justify-between gap-2">
                                            <span>Segment {index + 1}: {segment.title}</span>
                                        </AccordionTrigger>
                                        <AccordionContent className="flex flex-col gap-4">
                                            {audioUrl && (
                                                <div>
                                                    <span className="font-medium text-sm mb-2 block">Audio: </span>
                                                    <audio controls className="w-full" src={audioUrl}>
                                                        Your browser does not support the audio element.
                                                    </audio>
                                                </div>
                                            )}
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                                {segment.title && (
                                                    <div>
                                                        <span className="font-medium">Title: </span>
                                                        <span>{segment.title}</span>
                                                    </div>
                                                )}
                                                {segment.audio_duration && (
                                                    <div>
                                                        <span className="font-medium">Duration: </span>
                                                        <Badge variant="outline">{segment.audio_duration}s</Badge>
                                                    </div>
                                                )}
                                                {segment.word_count && (
                                                    <div>
                                                        <span className="font-medium">Word Count: </span>
                                                        <Badge variant="outline">{segment.word_count}</Badge>
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
        </div>
    );
}

