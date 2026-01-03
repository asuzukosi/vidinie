"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { IconPlus } from "@tabler/icons-react";
import { Loader2 } from "lucide-react";
import CreateTaskModal from "@/components/modals/CreateVideoPipelineModal";
import {CreateVideoPipelineRequest, VideoPipelineSummary } from "@/lib/sdk/types";
import TaskTable from "@/components/pipeline/VideoPipelineTable";
import { LoadingPage } from "@/components/utils/LoadingPage";
import client from "@/lib/sdk/client";
import type { PipelineTaskTableItem } from "@/components/pipeline/VideoPipelineTable";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function TasksPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [pipelineTasks, setPipelineTasks] = useState<VideoPipelineSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreatingTask, setIsCreatingTask] = useState(false);

  const createTask = async (task: CreateVideoPipelineRequest) => {
    setIsCreatingTask(true);
    try {
      console.log("creating video:", task);
      if (task.file) {
        const result: VideoPipelineSummary = await client.createVideoPipelineFromFile(task.name, task.description, 
          task.tags || [], task.projects || [], task.file);
        console.log("result:", result);
      } else {
        task.file = undefined;
        const result: VideoPipelineSummary = await client.createVideoPipelineFromUrl(task);
        console.log("result:", result);
      }
    } catch (error) {
      console.error("Error creating task:", error);
      throw error;
    } finally {
      setIsCreatingTask(false);
    }
  };

  const fetchPipelineTasks = async () => {
    setIsLoading(true);
    const result: VideoPipelineSummary[] = await client.getAllVideoPipelines();
    setPipelineTasks(result as VideoPipelineSummary[]);
    console.log("pipelineTasks:", result);
    setIsLoading(false);
  };

  useEffect(() => {
    fetchPipelineTasks().catch(console.error);
  }, []);

  // Check for create query parameter and open modal
  useEffect(() => {
    const createParam = searchParams.get("create");
    if (createParam === "true") {
      setIsModalOpen(true);
      // Remove the query parameter from URL without reloading
      router.replace("/tasks", { scroll: false });
    }
  }, [searchParams, router]);

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
          disabled={isCreatingTask}
          className="flex items-center gap-2 rounded-sm bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-100 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isCreatingTask ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Creating...
            </>
          ) : (
            <>
              <IconPlus className="h-4 w-4" />
              New Video
            </>
          )}
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
            <div className="flex items-center justify-center w-full">
              <Card className="w-full w-[80%]">
                <CardHeader className="text-center">
                  <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                    <IconPlus className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <CardTitle>No videos created yet</CardTitle>
                  <CardDescription className="mt-2">
                    Get started by creating your first video. Upload a document or provide a URL to begin.
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex justify-center">
                  <Button
                    onClick={() => setIsModalOpen(true)}
                    size="lg"
                    className="flex items-center gap-2"
                  >
                    <IconPlus className="h-5 w-5" />
                    Create Your First Video
                  </Button>
                </CardContent>
              </Card>
            </div>
          )}
        </>
      )}
      {/* create task modal */}
      <CreateTaskModal
        isOpen={isModalOpen}
        onClose={() => {
          if (!isCreatingTask) {
            setIsModalOpen(false);
          }
        }}
        onCreateTask={async (task: CreateVideoPipelineRequest) => {
          try {
            await createTask(task);
            await fetchPipelineTasks();
            setIsModalOpen(false);
          } catch (error) {
            console.error("Error creating task:", error);
            // keep modal open on error so user can retry
          }
        }}
      />
    </div>
  );
}