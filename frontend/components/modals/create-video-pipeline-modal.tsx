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
        <div className="relative z-10 w-full max-w-lg rounded-sm border border-zinc-200 bg-white p-6 shadow-2xl dark:border-zinc-800 dark:bg-zinc-900">
          {/* header */}
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-zinc-900 dark:text-white">
              Create New Video
            </h2>
            <button
              onClick={() => {
                if (!isCreating) {
                  onClose();
                }
              }}
              disabled={isCreating}
              className="rounded-lg p-1 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <IconX className="h-5 w-5" />
            </button>
          </div>
  
          {/* tabs */}
          <div className="mb-6 flex gap-2">
            <button
              onClick={() => setActiveTab(TaskType.URL)}
              className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === TaskType.URL
                  ? "bg-zinc-900 text-white dark:bg-white dark:text-zinc-900"
                  : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
              }`}
            >
              <IconFileText className="h-4 w-4" />
              Link to Article
            </button>
            <button
              onClick={() => setActiveTab(TaskType.UPLOAD)}
              className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === TaskType.UPLOAD
                  ? "bg-zinc-900 text-white dark:bg-white dark:text-zinc-900"
                  : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
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
                className=" resize-none rounded-lg border border-zinc-300 bg-white p-4 text-sm text-zinc-900 placeholder-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-white dark:placeholder-zinc-500"
              />
            </div>
          ) : (
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors ${
                dragActive
                  ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                  : selectedFile
                    ? "border-black-500 bg-black-50 dark:bg-black-900/20"
                    : "border-zinc-300 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800/50"
              }`}
            >
              {selectedFile ? (
                <>
                  <IconFileText className="mb-3 h-8 w-8 text-black-500" />
                  <p className="mb-1 text-sm font-medium text-zinc-700 dark:text-zinc-300">
                    {selectedFile.name}
                  </p>
                  <p className="mb-4 text-xs text-zinc-500 dark:text-zinc-400">
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
                  <IconUpload className="mb-3 h-10 w-10 text-zinc-400" />
                  <p className="mb-1 text-sm font-medium text-zinc-700 dark:text-zinc-300">
                    Drag and drop your file here
                  </p>
                  <p className="mb-4 text-xs text-zinc-500 dark:text-zinc-400">
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
                    className="cursor-pointer rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-100"
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
              className="rounded-lg px-4 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateTask}
              disabled={!canCreate || isCreating}
              className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                canCreate && !isCreating
                  ? "bg-zinc-900 text-white hover:bg-zinc-800 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-100"
                  : "cursor-not-allowed bg-zinc-300 text-zinc-500 dark:bg-zinc-700 dark:text-zinc-500"
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

