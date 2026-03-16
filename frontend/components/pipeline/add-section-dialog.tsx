"use client";

import { useState } from "react";
import { ContentSection } from "@/lib/sdk/types";
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

interface AddSectionDialogProps {
    videoPipelineId: string;
    onSuccess: () => void;
}

export function AddSectionDialog({ videoPipelineId, onSuccess }: AddSectionDialogProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [isAddingSection, setIsAddingSection] = useState(false);
    const [newSectionTitle, setNewSectionTitle] = useState("");
    const [newSectionContent, setNewSectionContent] = useState("");
    const [newSectionLevel, setNewSectionLevel] = useState(1);

    const handleAddSection = async () => {
        if (!newSectionTitle.trim() || !newSectionContent.trim()) {
            toast.error("Please fill in both title and content");
            return;
        }

        setIsAddingSection(true);
        try {
            const newSection: ContentSection = {
                title: newSectionTitle,
                content: newSectionContent,
                level: newSectionLevel,
            };
            await client.addVideoPipelineSection(videoPipelineId, newSection);
            toast.success("Section added successfully");
            setNewSectionTitle("");
            setNewSectionContent("");
            setNewSectionLevel(1);
            setIsOpen(false);
            onSuccess();
        } catch (error: any) {
            toast.error(error.message || "Failed to add section");
        } finally {
            setIsAddingSection(false);
        }
    };

    const handleCancel = () => {
        setNewSectionTitle("");
        setNewSectionContent("");
        setNewSectionLevel(1);
        setIsOpen(false);
    };

    return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
                <Button variant="outline" size="sm"
                    className="w-full flex items-center justify-center gap-2 text-xs border-dashed border-border text-muted-foreground hover:text-foreground hover:border-foreground/30">
                    <IconPlus className="size-4" />
                    Add New Section
                </Button>
            </DialogTrigger>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Add New Section</DialogTitle>
                    <DialogDescription>
                        Add a new section to the document content
                    </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                    <div>
                        <Label htmlFor="section-title">Title</Label>
                        <Input
                            id="section-title"
                            value={newSectionTitle}
                            onChange={(e) => setNewSectionTitle(e.target.value)}
                            placeholder="Section title"
                        />
                    </div>
                    <div>
                        <Label htmlFor="section-content">Content</Label>
                        <Textarea
                            id="section-content"
                            value={newSectionContent}
                            onChange={(e) => setNewSectionContent(e.target.value)}
                            placeholder="Section content"
                            rows={6}
                        />
                    </div>
                    <div>
                        <Label htmlFor="section-level">Level</Label>
                        <Input
                            id="section-level"
                            type="number"
                            min="1"
                            max="5"
                            value={newSectionLevel}
                            onChange={(e) => setNewSectionLevel(parseInt(e.target.value) || 1)}
                        />
                    </div>
                </div>
                <DialogFooter>
                    <Button
                        variant="outline"
                        onClick={handleCancel}
                        disabled={isAddingSection}
                    >
                        Cancel
                    </Button>
                    <Button
                        onClick={handleAddSection}
                        disabled={isAddingSection || !newSectionTitle.trim() || !newSectionContent.trim()}
                    >
                        {isAddingSection ? "Adding..." : "Add Section"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

