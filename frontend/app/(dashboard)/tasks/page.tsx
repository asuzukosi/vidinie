"use client";

import { useState, useRef } from "react";
import { IconPlus, IconUpload, IconFileText, IconX, IconFile } from "@tabler/icons-react";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";

// Task stages
type TaskStage = "parsing" | "content" | "script" | "video";

interface Task {
    id: string;
    name: string;
    description: string;
    stage: TaskStage;
    createdAt: Date;
    videoUrl?: string;
}

const stageLabels: Record<TaskStage, { label: string; step: number; color: string }> = {
    parsing: { label: "Parsing", step: 1, color: "bg-blue-500" },
    content: { label: "Content", step: 2, color: "bg-purple-500" },
    script: { label: "Script", step: 3, color: "bg-indigo-500" },
    video: { label: "Video", step: 4, color: "bg-green-500" },
};

const ALLOWED_FILE_TYPES = ".txt,.pdf,.html";
const ALLOWED_MIME_TYPES = ["text/plain", "application/pdf", "text/html"];

function StageIndicator({ stage }: { stage: TaskStage }) {
    const info = stageLabels[stage];
    return (
        <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium text-white ${info.color}`}>
            Stage {info.step}: {info.label}
        </span>
    );
}

interface CreateTaskModalProps {
    isOpen: boolean;
    onClose: () => void;
    onCreateTask: (name: string) => void;
}

function CreateTaskModal({ isOpen, onClose, onCreateTask }: CreateTaskModalProps) {
    const [activeTab, setActiveTab] = useState<"upload" | "paste">("upload");
    const [pastedContent, setPastedContent] = useState("");
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [dragActive, setDragActive] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

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

    const handleCreateTask = () => {
        let taskName = "";
        if (activeTab === "upload" && selectedFile) {
            taskName = selectedFile.name.replace(/\.[^/.]+$/, ""); // Remove extension
        } else if (activeTab === "paste" && pastedContent.trim()) {
            taskName = pastedContent.substring(0, 50).trim() || "Pasted Document";
        }

        if (taskName) {
            onCreateTask(taskName);
            setSelectedFile(null);
            setPastedContent("");
            onClose();
        }
    };

    const canCreate = (activeTab === "upload" && selectedFile) || (activeTab === "paste" && pastedContent.trim());

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="relative z-10 w-full max-w-lg rounded-xl border border-zinc-200 bg-white p-6 shadow-2xl dark:border-zinc-800 dark:bg-zinc-900">
                {/* Header */}
                <div className="mb-6 flex items-center justify-between">
                    <h2 className="text-xl font-semibold text-zinc-900 dark:text-white">Create New Task</h2>
                    <button
                        onClick={onClose}
                        className="rounded-lg p-1 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-300"
                    >
                        <IconX className="h-5 w-5" />
                    </button>
                </div>

                {/* Tabs */}
                <div className="mb-6 flex gap-2">
                    <button
                        onClick={() => setActiveTab("upload")}
                        className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${activeTab === "upload"
                            ? "bg-zinc-900 text-white dark:bg-white dark:text-zinc-900"
                            : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
                            }`}
                    >
                        <IconUpload className="h-4 w-4" />
                        Upload File
                    </button>
                    <button
                        onClick={() => setActiveTab("paste")}
                        className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${activeTab === "paste"
                            ? "bg-zinc-900 text-white dark:bg-white dark:text-zinc-900"
                            : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
                            }`}
                    >
                        <IconFileText className="h-4 w-4" />
                        Paste Document
                    </button>
                </div>

                {/* Content */}
                {activeTab === "upload" ? (
                    <div
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                        className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors ${dragActive
                            ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                            : selectedFile
                                ? "border-green-500 bg-green-50 dark:bg-green-900/20"
                                : "border-zinc-300 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800/50"
                            }`}
                    >
                        {selectedFile ? (
                            <>
                                <IconFile className="mb-3 h-10 w-10 text-green-500" />
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
                                    Supports .txt, .pdf, .html files
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
                ) : (
                    <div>
                        <textarea
                            value={pastedContent}
                            onChange={(e) => setPastedContent(e.target.value)}
                            placeholder="Paste your document content here..."
                            className="h-48 w-full resize-none rounded-lg border border-zinc-300 bg-white p-4 text-sm text-zinc-900 placeholder-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-white dark:placeholder-zinc-500"
                        />
                    </div>
                )}

                {/* Actions */}
                <div className="mt-6 flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="rounded-lg px-4 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleCreateTask}
                        disabled={!canCreate}
                        className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${canCreate
                            ? "bg-zinc-900 text-white hover:bg-zinc-800 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-100"
                            : "cursor-not-allowed bg-zinc-300 text-zinc-500 dark:bg-zinc-700 dark:text-zinc-500"
                            }`}
                    >
                        Create Task
                    </button>
                </div>
            </div>
        </div>
    );
}

// Simulate task progression through stages
function useTaskSimulation() {
    const [tasks, setTasks] = useState<Task[]>([]);

    const createTask = (name: string) => {
        const newTask: Task = {
            id: Date.now().toString(),
            name,
            description: "Processing video content from uploaded document",
            stage: "parsing",
            createdAt: new Date(),
        };
        setTasks(prev => [newTask, ...prev]);

        // Simulate stage progression
        const stages: TaskStage[] = ["parsing", "content", "script", "video"];
        let currentStageIndex = 0;

        const progressTask = () => {
            currentStageIndex++;
            if (currentStageIndex < stages.length) {
                setTasks(prev =>
                    prev.map(t =>
                        t.id === newTask.id
                            ? { ...t, stage: stages[currentStageIndex] }
                            : t
                    )
                );
                // Random delay between 2-4 seconds for each stage
                setTimeout(progressTask, 2000 + Math.random() * 2000);
            }
        };

        // Start progression after 2-3 seconds
        setTimeout(progressTask, 2000 + Math.random() * 1000);
    };

    return { tasks, createTask };
}

export default function TasksPage() {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const { tasks, createTask } = useTaskSimulation();

    return (
        <div>
            {/* Header */}
            <div className="mb-8 flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">Tasks</h1>
                    <p className="mt-2 text-zinc-600 dark:text-zinc-400">
                        Manage your ongoing tasks.
                    </p>
                </div>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="flex items-center gap-2 rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-100"
                >
                    <IconPlus className="h-4 w-4" />
                    New Task
                </button>
            </div>

            {/* Tasks List */}
            {tasks.length === 0 ? (
                <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-zinc-300 bg-zinc-50 py-16 dark:border-zinc-700 dark:bg-zinc-900/50">
                    <p className="mb-2 text-zinc-600 dark:text-zinc-400">No ongoing tasks</p>
                    <p className="text-sm text-zinc-500 dark:text-zinc-500">
                        Click the + button to create a new task
                    </p>
                </div>
            ) : (
                <div className="rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="font-semibold">Name</TableHead>
                                <TableHead className="font-semibold">Description</TableHead>
                                <TableHead className="font-semibold">Date</TableHead>
                                <TableHead className="font-semibold">Status</TableHead>
                                <TableHead className="font-semibold">Video</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {tasks.map((task) => (
                                <TableRow key={task.id}>
                                    <TableCell className="font-medium text-zinc-900 dark:text-white">
                                        {task.name}
                                    </TableCell>
                                    <TableCell className="text-zinc-600 dark:text-zinc-400">
                                        {task.description}
                                    </TableCell>
                                    <TableCell className="text-zinc-600 dark:text-zinc-400">
                                        {task.createdAt.toLocaleDateString()}
                                    </TableCell>
                                    <TableCell>
                                        <StageIndicator stage={task.stage} />
                                    </TableCell>
                                    <TableCell className="text-zinc-600 dark:text-zinc-400">
                                        {task.videoUrl || "N/A"}
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </div>
            )}

            {/* Modal */}
            <CreateTaskModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onCreateTask={createTask}
            />
        </div>
    );
}
