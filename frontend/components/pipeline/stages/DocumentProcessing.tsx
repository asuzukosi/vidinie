"use client";

import { ImageMetadata, ParsedContent } from "@/lib/sdk/types";
import { Badge } from "@/components/ui/badge"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import Markdown from 'react-markdown'
import Image from 'next/image'
import client from "@/lib/sdk/client"

function capitalizeFirstChar(str: string): string {
    // capitalize the first character of the string
    if (!str) return str;
    return str.charAt(0).toUpperCase() + str.slice(1);
}

interface DocumentProcessingProps {
    content?: ParsedContent;
    images?: ImageMetadata[];
}

export function DocumentProcessing({ content, images }: DocumentProcessingProps) {

    return (
        <div className="space-y-8">
            <div className="max-w-4xl mx-auto">
                <div className="flex flex-col gap-6">
                    <div className="space-y-4">
                        <h3 className="font-semibold text-md">
                            {content?.title}
                        </h3>
                        <div className="flex flex-row justify-end gap-2 text-xs  max-w-full whitespace-pre-wrap break-words">
                            <Badge variant="outline">{content?.total_pages} {content?.total_pages === 1 ? "page" : "pages"}</Badge>
                            <Badge variant="outline">{content?.sections.length} {content?.sections.length === 1 ? "section" : "sections"}</Badge>
                        </div>
                        <div className="space-y-4 mb-4">
                        <h3 className="font-semibold text-sm">Sections</h3>
                        <Accordion
                            type="single"
                            collapsible
                            className="w-full"
                            defaultValue="item-1"
                            >
                            {content?.sections.map((section, index) => (
                                <AccordionItem key={index} value={capitalizeFirstChar(section.title || `section-${index}`)}>
                                    <AccordionTrigger className="text-sm flex flex-row justify-between gap-2">
                                        <span>{capitalizeFirstChar(section.title || `Section ${index + 1}`)}</span> 
                                    </AccordionTrigger>
                                    <AccordionContent className="flex flex-col gap-4 text-balance">
                                        <Badge variant="outline">{section.level} {section.level === 1 ? "level" : "levels"}</Badge>
                                        <Markdown>{section.content}</Markdown>
                                    </AccordionContent>
                                </AccordionItem>
                            ))}
                        </Accordion>
                        </div>
                        <div className="space-y-4 mb-4">
                            <h3 className="font-semibold text-sm">Images</h3>
                            {images && images.length > 0 ? (
                                <Accordion
                                    type="single"
                                    collapsible
                                    className="w-full"
                                >
                                    {images.map((image, index) => {
                                        const imageUrl = image.filepath ? client.getLinkToImage(image.filepath) : '';
                                        console.log("imageUrl:", imageUrl);
                                        return (
                                            <AccordionItem key={index} value={`image-${index}`}>
                                                <AccordionTrigger className="text-sm flex flex-row justify-between gap-2">
                                                    <span>{image.label}</span>
                                                </AccordionTrigger>
                                                <AccordionContent className="flex flex-col gap-4">
                                                    {imageUrl && (
                                                        <div className="relative h-64 rounded-lg overflow-hidden">
                                                            <Image
                                                                src={imageUrl}
                                                                alt={image.filename}
                                                                fill
                                                                className="object-contain"
                                                                unoptimized
                                                            />
                                                        </div>
                                                    )}
                                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                                        {image.label && (
                                                            <div>
                                                                <span className="font-medium">Label: </span>
                                                                <span>{image.label}</span>
                                                            </div>
                                                        )}
                                                        {image.ai_relevance && (
                                                            <div>
                                                                <span className="font-medium">AI Relevance: </span>
                                                                <Badge variant="outline">{image.ai_relevance}</Badge>
                                                            </div>
                                                        )}
                                                        {image.description && (
                                                            <div className="md:col-span-2">
                                                                <span className="font-medium">Description: </span>
                                                                <span>{image.description}</span>
                                                            </div>
                                                        )}
                                                        {image.format && (
                                                            <div>
                                                                <span className="font-medium">Format: </span>
                                                                <Badge variant="outline">{image.format}</Badge>
                                                            </div>
                                                        )}
                                                        {image.image_type && (
                                                            <div>
                                                                <span className="font-medium">Image Type: </span>
                                                                <Badge variant="outline">{image.image_type}</Badge>
                                                            </div>
                                                        )}
                                                        {image.index_on_page !== undefined && (
                                                            <div>
                                                                <span className="font-medium">Index on Page: </span>
                                                                <Badge variant="outline">{image.index_on_page}</Badge>
                                                            </div>
                                                        )}
                                                        {image.page_number !== undefined && (
                                                            <div>
                                                                <span className="font-medium">Page Number: </span>
                                                                <Badge variant="outline">{image.page_number}</Badge>
                                                            </div>
                                                        )}
                                                        {image.key_elements && image.key_elements.length > 0 && (
                                                            <div className="md:col-span-2">
                                                                <span className="font-medium">Key Elements: </span>
                                                                <div className="flex flex-wrap gap-1 mt-1">
                                                                    {image.key_elements.map((element, idx) => (
                                                                        <Badge key={idx} variant="secondary">
                                                                            {element}
                                                                        </Badge>
                                                                    ))}
                                                                </div>
                                                            </div>
                                                        )}
                                                        {image.text_context && (
                                                            <div className="md:col-span-2">
                                                                <span className="font-medium">Text Context: </span>
                                                                <p className="mt-1 text-muted-foreground whitespace-pre-wrap">{image.text_context}</p>
                                                            </div>
                                                        )}
                                                        {image.width && image.height && (
                                                            <div>
                                                                <span className="font-medium">Dimensions: </span>
                                                                <span>{image.width} x {image.height}</span>
                                                            </div>
                                                        )}
                                                        {image.size_bytes && (
                                                            <div>
                                                                <span className="font-medium">Size: </span>
                                                                <span>{(image.size_bytes / 1024).toFixed(2)} KB</span>
                                                            </div>
                                                        )}
                                                    </div>
                                                </AccordionContent>
                                            </AccordionItem>
                                        );
                                    })}
                                </Accordion>
                            ) : (
                                <p className="text-sm text-muted-foreground">No images found</p>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
