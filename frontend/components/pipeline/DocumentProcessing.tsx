"use client";

import { useState } from "react";
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
import { IconTrash } from "@tabler/icons-react";
import { toast } from "sonner";
import client from "@/lib/sdk/client";
import { AddImageDialog } from "@/components/pipeline/AddImageDialog";
import { AddSectionDialog } from "@/components/pipeline/AddSectionDialog";

interface DocumentProcessingProps {
    content?: VideoPipelineParsedContent;
    images?: VideoPipelineImageMetadata[];
    videoPipelineId: string;
    onRefresh: () => void;
}

export function DocumentProcessing({ content, images, videoPipelineId, onRefresh }: DocumentProcessingProps) {
    const [isDeletingImage, setIsDeletingImage] = useState<number | null>(null);
    const [isDeletingSection, setIsDeletingSection] = useState<number | null>(null);

    const handleDeleteImage = async (index: number) => {
        setIsDeletingImage(index);
        try {
            await client.deleteVideoPipelineImage(videoPipelineId, index);
            toast.success("Image deleted successfully");
            setIsDeletingImage(null);
            onRefresh();
        } catch (error: any) {
            toast.error(error.message || "Failed to delete image");
            setIsDeletingImage(null);
        }
    };

    const handleDeleteSection = async (index: number) => {
        setIsDeletingSection(index);
        try {
            await client.deleteVideoPipelineSection(videoPipelineId, index);
            toast.success("Section deleted successfully");
            setIsDeletingSection(null);
            onRefresh();
        } catch (error: any) {
            toast.error(error.message || "Failed to delete section");
            setIsDeletingSection(null);
        }
    };

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
                                        <div className="flex items-center gap-2 flex-1">
                                            <span className="italic font-light">{capitalizeFirstChar(section.title || `Section ${index + 1}`)}</span>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                className="h-6 w-6 p-0 text-destructive hover:text-destructive"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    if (confirm(`Are you sure you want to delete section "${section.title}"?`)) {
                                                        handleDeleteSection(index);
                                                    }
                                                }}
                                                disabled={isDeletingSection === index}
                                            >
                                                <IconTrash className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </AccordionTrigger>
                                    <AccordionContent className="flex flex-col gap-4 text-balance italic">
                                        <Badge variant="outline">{section.level} {section.level === 1 ? "level" : "levels"}</Badge>
                                        <Markdown>{section.content}</Markdown>
                                    </AccordionContent>
                                </AccordionItem>
                            ))}
                        </Accordion>
                        <AddSectionDialog 
                            videoPipelineId={videoPipelineId}
                            onSuccess={onRefresh}
                        />
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
                                        <DocumentProcessingImage 
                                            key={index} 
                                            image={image} 
                                            index={index}
                                            onDelete={() => {
                                                if (confirm(`Are you sure you want to delete image "${image.label || image.filename}"?`)) {
                                                    handleDeleteImage(index);
                                                }
                                            }}
                                            isDeleting={isDeletingImage === index}
                                        />
                                    ))}
                                </Accordion>
                            ) : (
                                <p className="text-sm text-muted-foreground">No images found</p>
                            )}
                            <AddImageDialog 
                                videoPipelineId={videoPipelineId}
                                onSuccess={onRefresh}
                            />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
