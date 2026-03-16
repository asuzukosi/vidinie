"use client";
import { useState, useRef, useMemo, useEffect } from "react";
import { IconX, IconUpload, IconFileText} from "@tabler/icons-react";
import { Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { FieldGroup } from "@/components/ui/field";
import { Field } from "@/components/ui/field";
import { FieldLabel } from "@/components/ui/field";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CreateVideoPipelineRequest, AudioVoice } from "@/lib/sdk/types";
import { toast } from "sonner";
import { useSelector } from "react-redux";
import type { RootState } from "@/lib/store/store";
import posthog from 'posthog-js';
import { PostHogEvent } from "@/lib/utils";

const ALLOWED_FILE_TYPES = ".pdf";
const ALLOWED_MIME_TYPES = ["application/pdf"];

interface CreateTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateTask: (task: CreateVideoPipelineRequest) => void;
}

enum TaskType {
    UPLOAD = "upload",
    URL = "url",
}
export default function CreateVideoPipelineModal({
    isOpen,
    onClose,
    onCreateTask,
  }: CreateTaskModalProps) {
    const [activeTab, setActiveTab] = useState<TaskType>(TaskType.URL);
    const [name, setName] = useState("");
    const [instructions, setInstructions] = useState("");
    const [voice, setVoice] = useState<AudioVoice>("Narrative Expressive Male");
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [selectedUrl, setSelectedUrl] = useState("");
    const [dragActive, setDragActive] = useState(false);
    const [isCreating, setIsCreating] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const audioRef = useRef<HTMLAudioElement>(null);
    const user = useSelector((state: RootState) => state.auth.user);

    // convert voice name to file path (e.g., "Narrative Expressive Male" -> "narrative_expressive_male.mp3")
    const getVoiceSamplePath = (voiceName: AudioVoice): string => {
      const fileName = voiceName.toLowerCase().replace(/\s+/g, "_") + ".mp3";
      return `/voice_samples/${fileName}`;
    };

    // update audio source when voice changes
    useEffect(() => {
      if (audioRef.current) {
        audioRef.current.load();
      }
    }, [voice]);

    useEffect(() => {
      posthog.capture(PostHogEvent.CREATE_VIDEO_PIPELINE_CREATION_STARTED, {
        category: "video_pipeline",
        label: user?.email || "unknown",
        value: 1,
      });
    }, [user]);
  
    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file && ALLOWED_MIME_TYPES.includes(file.type)) {
        setSelectedFile(file);
      }
    };
  
    const handleDrag = (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (e.type === "dragenter" || e.type === "dragover") {
        setDragActive(true);
      } else if (e.type === "dragleave") {
        setDragActive(false);
      }
    };
  
    const handleDrop = (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);
      const file = e.dataTransfer.files?.[0];
      if (file && ALLOWED_MIME_TYPES.includes(file.type)) {
        setSelectedFile(file);
      }
    };
  
    const handleCreateTask = async () => {
      if (name.trim() && instructions.trim()) {
        setIsCreating(true);
        try {
          await onCreateTask({
            name: name,
            instructions: instructions,
            voice: voice,
            url: selectedUrl || undefined,
            file: selectedFile || undefined,
          });
          setSelectedFile(null);
          setSelectedUrl("");
          setName("");
          setInstructions("");
          setVoice("Narrative Expressive Male");
        } catch (error) {
        } finally {
          setIsCreating(false);
        }
      } else {
        toast.error("Please fill in all fields");
      }
    };
  
    const canCreate = useMemo(() => {
      return name.trim() && instructions.trim() && ((activeTab === TaskType.UPLOAD && selectedFile) ||
      (activeTab === TaskType.URL && selectedUrl.trim()));
    }, [activeTab, selectedFile, selectedUrl, name, instructions]);
  
    if (!isOpen) return null;
  
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        {/* backdrop */}
        <div
          className="absolute inset-0 bg-black/50 backdrop-blur-sm"
          onClick={() => {
            if (!isCreating) {
              onClose();
            }
          }}
        />
  
        {/* modal */}
        <div className="relative z-10 w-full max-w-lg rounded-none border border-border bg-card p-6 shadow-2xl backdrop-blur-[14px]">
          {/* header */}
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-foreground">
              Create New Video
            </h2>
            <button
              onClick={() => {
                if (!isCreating) {
                  onClose();
                }
              }}
              disabled={isCreating}
              className="rounded-none p-1 text-muted-foreground hover:bg-accent hover:text-accent-foreground disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <IconX className="h-5 w-5" />
            </button>
          </div>

          {/* tabs */}
          <div className="mb-6 flex gap-2">
            <button
              onClick={() => setActiveTab(TaskType.URL)}
              className={`flex items-center gap-2 rounded-none px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === TaskType.URL
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              }`}
            >
              <IconFileText className="h-4 w-4" />
              Link to Article
            </button>
            <button
              onClick={() => setActiveTab(TaskType.UPLOAD)}
              className={`flex items-center gap-2 rounded-none px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === TaskType.UPLOAD
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              }`}
            >
              <IconUpload className="h-4 w-4" />
              Upload PDF File
            </button>
          </div>
          {/* content input */}
          {activeTab === TaskType.URL ? (
            <div>
              <FieldLabel htmlFor="url">
                  Link
              </FieldLabel>
              <Input
                id="url"
                value={selectedUrl}
                onChange={(e) => setSelectedUrl(e.target.value)}
                placeholder="Paste link to the article..."
                className="resize-none rounded-none border border-input bg-input-bg p-4 text-sm text-foreground placeholder-muted-foreground focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring"
              />
            </div>
          ) : (
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`flex flex-col items-center justify-center rounded-none border-2 border-dashed p-8 transition-colors ${
                dragActive
                  ? "border-primary bg-accent"
                  : selectedFile
                    ? "border-primary bg-accent"
                    : "border-border bg-muted"
              }`}
            >
              {selectedFile ? (
                <>
                  <IconFileText className="mb-3 h-8 w-8 text-primary" />
                  <p className="mb-1 text-sm font-medium text-foreground">
                    {selectedFile.name}
                  </p>
                  <p className="mb-4 text-xs text-muted-foreground">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </p>
                  <button
                    onClick={() => setSelectedFile(null)}
                    className="text-sm text-red-500 hover:text-red-600"
                  >
                    Remove
                  </button>
                </>
              ) : (
                <>
                  <IconUpload className="mb-3 h-10 w-10 text-muted-foreground" />
                  <p className="mb-1 text-sm font-medium text-foreground">
                    Drag and drop your file here
                  </p>
                  <p className="mb-4 text-xs text-muted-foreground">
                    Supports .pdf files
                  </p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept={ALLOWED_FILE_TYPES}
                    onChange={handleFileChange}
                    className="hidden"
                    id="file-upload"
                  />
                  <label
                    htmlFor="file-upload"
                    className="cursor-pointer rounded-none bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
                  >
                    Browse Files
                  </label>
                </>
              )}
            </div>
          )}
          {/* fields */}
          <div className="mb-6">
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="name">
                  Name
                </FieldLabel>
                <Input
                  id="name"
                  placeholder="Enter your name for the video"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="instructions">
                  Instructions
                </FieldLabel>
                <Textarea
                  id="instructions"
                  placeholder="Enter instructions to guide the model (e.g., focus on key concepts, emphasize practical examples, use certain tone or imagery). The more detailed the instructions, the better the video will be."
                  required
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  rows={6}
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="voice">
                  Voice
                </FieldLabel>
                <Select value={voice} onValueChange={(value) => setVoice(value as AudioVoice)}>
                  <SelectTrigger id="voice" className="w-full">
                    <SelectValue placeholder="Select a voice" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Narrative Expressive Male">Narrative Expressive Male</SelectItem>
                    <SelectItem value="Fun Vibrant Female">Fun Vibrant Female</SelectItem>
                    <SelectItem value="Calm Narrative Male">Calm Narrative Male</SelectItem>
                    <SelectItem value="Calm Soothing Female">Calm Soothing Female</SelectItem>
                    <SelectItem value="Soothing British Male">Soothing British Male</SelectItem>
                    <SelectItem value="Expressive Professional Male">Expressive Professional Male</SelectItem>
                  </SelectContent>
                </Select>
                <div className="mt-2">
                  <audio
                    ref={audioRef}
                    src={getVoiceSamplePath(voice)}
                    controls
                    className="w-full"
                  />
                </div>
              </Field>
            </FieldGroup>
            </div>
  
          {/* actions */}
          <div className="mt-6 flex justify-end gap-3">
            <button
              onClick={onClose}
              disabled={isCreating}
              className="rounded-none px-4 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateTask}
              disabled={!canCreate || isCreating}
              className={`flex items-center gap-2 rounded-none px-4 py-2 text-sm font-medium transition-colors ${
                canCreate && !isCreating
                  ? "bg-primary text-primary-foreground hover:bg-primary/90"
                  : "cursor-not-allowed bg-muted text-muted-foreground"
              }`}
            >
              {isCreating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                "Create Video"
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

