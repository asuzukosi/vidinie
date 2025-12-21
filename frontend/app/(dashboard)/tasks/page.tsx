"use client";

import { useState } from "react";
import { IconPlus } from "@tabler/icons-react";
import CreateTaskModal from "@/components/pipeline/CreateTaskModal";
import { StartPipelineRequest } from "@/lib/sdk/types";

export default function TasksPage() {
    const [isModalOpen, setIsModalOpen] = useState(false);
    
    const createTask = (task: StartPipelineRequest) => {
      console.log(task);
    };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">
            Videos
          </h1>
          <p className="mt-2 text-zinc-600 dark:text-zinc-400">
            Manage your ongoing videos.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 rounded-sm bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-100"
        >
          <IconPlus className="h-4 w-4" />
          New Video
        </button>
      </div>
         place table here
      {/* create task modal */}
      <CreateTaskModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreateTask={createTask}
      />
    </div>
  );
}
