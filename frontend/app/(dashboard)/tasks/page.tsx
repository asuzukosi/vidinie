"use client";

import { useEffect, useState } from "react";
import { IconPlus } from "@tabler/icons-react";
import CreateTaskModal from "@/components/pipeline/CreateTaskModal";
import {StartPipelineRequest, SummaryPipelineDataResponse } from "@/lib/sdk/types";
import TaskTable from "@/components/TaskTable";
import { LoadingPage } from "@/components/LoadingPage";
import client from "@/lib/sdk/client";
import type { PipelineTaskTableItem } from "@/components/TaskTable";

const createTask = async (task: StartPipelineRequest) => {
  console.log("creating video:", task);
  if (task.file) {
    const result: SummaryPipelineDataResponse = await client.startPipelineWithFile(task.name, task.description, 
      task.tags || [], task.projects || [], task.file);
    console.log("result:", result);
  } else {
    task.file = undefined;
    const result: SummaryPipelineDataResponse = await client.startPipelieWithUrl(task);
    console.log("result:", result);
  }
};

export default function TasksPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [pipelineTasks, setPipelineTasks] = useState<SummaryPipelineDataResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchPipelineTasks = async () => {
    setIsLoading(true);
    const result: SummaryPipelineDataResponse[] = await client.getAllPipelines();
    setPipelineTasks(result as SummaryPipelineDataResponse[]);
    console.log("pipelineTasks:", result);
    setIsLoading(false);
  };

  useEffect(() => {
    fetchPipelineTasks().catch(console.error);
  }, []);

  return (
    <div className="p-6">
      {/* header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">
            Videos
          </h1>
          <p className="mt-2 text-zinc-600 dark:text-zinc-400">
            Manage your videos.
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
      {isLoading ? (
        <LoadingPage />
      ) : (
        <>
          {pipelineTasks.length > 0 ? (
            <TaskTable pipelineTasks={pipelineTasks as PipelineTaskTableItem[]} 
            />
          ) : (
            <div className="flex items-center justify-center h-full">
              <p className="text-zinc-600 dark:text-zinc-400">No videos found</p>
            </div>
          )}
        </>
      )}
      {/* create task modal */}
      <CreateTaskModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreateTask={(task: StartPipelineRequest) => {
          createTask(task).catch(console.error);
          fetchPipelineTasks().catch(console.error);
          setIsModalOpen(false);
        }}
      />
    </div>
  );
}