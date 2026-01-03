"use client";

import { VideoPipelineImageMetadata } from "@/lib/sdk/types";
import { Badge } from "@/components/ui/badge";
import {
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import Image from "next/image";
import { getLinkToImage } from "@/lib/utils";

interface DocumentProcessingImageProps {
  image: VideoPipelineImageMetadata;
  index: number;
}

export function DocumentProcessingImage({ image, index }: DocumentProcessingImageProps) {
  return (
    <AccordionItem value={`image-${index}`}>
      <AccordionTrigger className="text-sm flex flex-row justify-between gap-2">
        <span className="italic font-light">{image.label}</span>
      </AccordionTrigger>
      <AccordionContent className="flex flex-col gap-4">
        {getLinkToImage(image.filepath) && (
          <div className="relative h-64 rounded-lg overflow-hidden">
            <Image
              src={getLinkToImage(image.filepath)}
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
                {image.key_elements.map((element: string, idx: number) => (
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
}

