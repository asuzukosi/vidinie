"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { IconPlus } from "@tabler/icons-react";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import client from "@/lib/sdk/client";
import { toast } from "sonner";

interface AddImageDialogProps {
    videoPipelineId: string;
    onSuccess: () => void;
}

export function AddImageDialog({ videoPipelineId, onSuccess }: AddImageDialogProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [isAddingImage, setIsAddingImage] = useState(false);
    const [newImageFile, setNewImageFile] = useState<File | null>(null);
    const [newImageTextContext, setNewImageTextContext] = useState("");
    const [newImageLabel, setNewImageLabel] = useState(false);

    const handleAddImage = async () => {
        if (!newImageFile) {
            toast.error("Please select an image file");
            return;
        }

        setIsAddingImage(true);
        try {
            await client.addVideoPipelineImage(
                videoPipelineId,
                newImageFile,
                newImageTextContext,
                newImageLabel
            );
            toast.success("Image added successfully");
            setNewImageFile(null);
            setNewImageTextContext("");
            setNewImageLabel(false);
            setIsOpen(false);
            onSuccess();
        } catch (error: any) {
            toast.error(error.message || "Failed to add image");
        } finally {
            setIsAddingImage(false);
        }
    };

    const handleCancel = () => {
        setNewImageFile(null);
        setNewImageTextContext("");
        setNewImageLabel(false);
        setIsOpen(false);
    };

    return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
                <Button variant="outline" size="sm"
                    className="w-full flex items-center justify-center gap-2 text-xs border-dashed border-border text-muted-foreground hover:text-foreground hover:border-foreground/30">
                    <IconPlus className="size-4" />
                    Add New Image
                </Button>
            </DialogTrigger>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Add New Image</DialogTitle>
                    <DialogDescription>
                        Upload an image to add to the document
                    </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                    <div>
                        <Label htmlFor="image-file">Image File</Label>
                        <Input
                            id="image-file"
                            type="file"
                            accept="image/png,image/jpeg,image/jpg,image/gif"
                            onChange={(e) => {
                                const file = e.target.files?.[0];
                                if (file) {
                                    setNewImageFile(file);
                                }
                            }}
                        />
                    </div>
                    <div>
                        <Label htmlFor="image-text-context">Text Context (Optional)</Label>
                        <Textarea
                            id="image-text-context"
                            value={newImageTextContext}
                            onChange={(e) => setNewImageTextContext(e.target.value)}
                            placeholder="Surrounding text context for the image"
                            rows={3}
                        />
                    </div>
                    <div className="flex items-center gap-2">
                        <input
                            type="checkbox"
                            id="image-label"
                            checked={newImageLabel}
                            onChange={(e) => setNewImageLabel(e.target.checked)}
                            className="rounded"
                        />
                        <Label htmlFor="image-label" className="cursor-pointer">
                            Label image with AI
                        </Label>
                    </div>
                </div>
                <DialogFooter>
                    <Button
                        variant="outline"
                        onClick={handleCancel}
                        disabled={isAddingImage}
                    >
                        Cancel
                    </Button>
                    <Button
                        onClick={handleAddImage}
                        disabled={isAddingImage || !newImageFile}
                    >
                        {isAddingImage ? "Adding..." : "Add Image"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

