"use client";

import { VideoPipelineImageMetadata,
         VideoPipelineParsedContent, 
         VideoPipelineContentSection } from "@/lib/sdk/types";
import { Badge } from "@/components/ui/badge"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import Markdown from 'react-markdown'
import { capitalizeFirstChar } from "@/lib/utils"
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { DocumentProcessingImage } from "./DocumentProcessingImage";
import { Button } from "@/components/ui/button";
import { IconPlus } from "@tabler/icons-react";
import { toast } from "sonner";
interface DocumentProcessingProps {
    content?: VideoPipelineParsedContent;
    images?: VideoPipelineImageMetadata[];
}

export function DocumentProcessing({ content, images }: DocumentProcessingProps) {

    if (!content) {
        return (
            <div className="space-y-8 w-full text-sm">
            <Card className="w-full text-sm">
                <CardHeader>
                    <CardTitle>Document Processing</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-muted-foreground">No content found. Re-run the pipeline task to generate the content.</p>
                </CardContent>
            </Card>
            </div>
        )
    }

    return (
        <div className="space-y-8">
            <div className="max-w-4xl mx-auto">
                <div className="flex flex-col gap-6">
                    <div className="space-y-4">
                        <h3 className="text-md">
                            {content.title}
                        </h3>
                        <div className="flex flex-row justify-end gap-2 text-xs  max-w-full whitespace-pre-wrap break-words">
                            <Badge variant="outline">{content.total_pages} {content.total_pages === 1 ? "page" : "pages"}</Badge>
                            <Badge variant="outline">{content.sections.length} {content.sections.length === 1 ? "section" : "sections"}</Badge>
                        </div>
                        <div className="space-y-4 mb-4">
                        <h3 className="font-semibold text-sm">Sections</h3>
                        <Accordion
                            type="single"
                            collapsible
                            className="w-full"
                            defaultValue="item-1"
                            >
                            {content?.sections.map((section: VideoPipelineContentSection, index: number) => (
                                <AccordionItem key={index} value={capitalizeFirstChar(section.title || `section-${index}`)} className="text-sm">
                                    <AccordionTrigger className="text-sm flex flex-row justify-between gap-2">
                                        <span className="italic font-light">{capitalizeFirstChar(section.title || `Section ${index + 1}`)}</span> 
                                    </AccordionTrigger>
                                    <AccordionContent className="flex flex-col gap-4 text-balance italic">
                                        <Badge variant="outline">{section.level} {section.level === 1 ? "level" : "levels"}</Badge>
                                        <Markdown>{section.content}</Markdown>
                                    </AccordionContent>
                                </AccordionItem>
                            ))}
                        </Accordion>
                        <Button variant="outline" size="sm"
                            onClick={() => toast.success("Section addtion implemented yet")}
                            className="w-full flex items-center justify-center gap-2 text-xs border-dashed border-zinc-300 text-zinc-500 hover:text-zinc-700 hover:border-zinc-500">
                            <IconPlus className="size-4" />
                            Add New Section
                        </Button>
                        </div>
                        <div className="space-y-4 mb-4">
                            <h3 className="font-semibold text-sm">Images</h3>
                            {images && images.length > 0 ? (
                                <Accordion
                                    type="single"
                                    collapsible
                                    className="w-full"
                                >
                                    {images.map((image, index) => (
                                        <DocumentProcessingImage key={index} image={image} index={index} />
                                    ))}
                                </Accordion>
                            ) : (
                                <p className="text-sm text-muted-foreground">No images found</p>
                            )}
                        <Button variant="outline" size="sm"
                            onClick={() => toast.success("Image addtion implemented yet")}
                            className="w-full flex items-center justify-center gap-2 text-xs border-dashed border-zinc-300 text-zinc-500 hover:text-zinc-700 hover:border-zinc-500">
                            <IconPlus className="size-4" />
                            Add New Image
                        </Button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
