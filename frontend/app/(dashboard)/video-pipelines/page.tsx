"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { IconPlus } from "@tabler/icons-react";
import { Loader2 } from "lucide-react";
import CreateTaskModal from "@/components/modals/create-video-pipeline-modal";
import {CreateVideoPipelineRequest, VideoPipelineSummary } from "@/lib/sdk/types";
import VideoPipelineTable from "@/components/pipeline/video-pipeline-table";
import { LoadingPage } from "@/components/utils/loading-page";
import client from "@/lib/sdk/client";
import type { VideoPipelineTableItem } from "@/components/pipeline/video-pipeline-table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import posthog from 'posthog-js';
import { useSelector, useDispatch } from "react-redux";
import { PostHogEvent } from "@/lib/utils";
import type { RootState } from "@/lib/store/store";
import { updateVideosRemaining, updateVideosGenerated } from "@/lib/store/slices/auth-slice";
import { authClient } from "@/lib/auth-client";

export default function TasksPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [videoPipelines, setVideoPipelines] = useState<VideoPipelineSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreatingTask, setIsCreatingTask] = useState(false);
  const user = useSelector((state: RootState) => state.auth.user);
  const dispatch = useDispatch();

  const createTask = async (task: CreateVideoPipelineRequest) => {

    setIsCreatingTask(true);
    try {
      if (task.file) {
        await client.createVideoPipelineFromFile(task.name, task.instructions, task.voice, task.file);
      } else {
        task.file = undefined;
        await client.createVideoPipelineFromUrl(task);
      }
      
      // update video counts after successful pipeline creation using Better Auth
      const newVideosRemaining = (user?.videos_remaining || 0) - 1;
      const newVideosGenerated = (user?.videos_generated || 0) + 1;
      
      try {
        // update user fields using better-auth client SDK
        const result = await authClient.updateUser({
          videos_remaining: newVideosRemaining,
          videos_generated: newVideosGenerated,
        });
        
        if (result?.error) {
          throw new Error(result.error.message || "Failed to update video counts");
        }
        
        // update Redux state
        dispatch(updateVideosRemaining(newVideosRemaining));
        dispatch(updateVideosGenerated(newVideosGenerated));
      } catch (error) {
        console.error("Error updating video counts:", error);
      }
    } catch (error) {
      console.error("Error creating task:", error);
      toast.error((error as Error).message.replace("Error: ", ""));
    } finally {
      setIsCreatingTask(false);
      posthog.capture(PostHogEvent.CREATE_VIDEO_PIPELINE_CREATION_COMPLETED, {
        category: "video_pipeline",
        label: user?.email || "unknown",
        value: 1,
      });
    }
  };

  const fetchVideoPipelines = async () => {

    setIsLoading(true);
    const result: VideoPipelineSummary[] = await client.getAllVideoPipelines();
    setVideoPipelines(result as VideoPipelineSummary[]);
    setIsLoading(false);
  };

  const handleCreateVideoPipeline = async (task: CreateVideoPipelineRequest) => {
    try {
      await createTask(task);
      await fetchVideoPipelines();
      setIsModalOpen(false);
    } catch (error) {
      console.error("Error creating task:", error);
      // keep modal open on error so user can retry
    }
  };

  const handleDeleteVideoPipeline = async (videoPipeline: VideoPipelineTableItem) => {
    try {
      await client.deleteVideoPipeline(videoPipeline.id);
    } catch (error) {
      console.error("Error deleting video pipeline:", error);
      throw error;
    }
  };

  useEffect(() => {
    fetchVideoPipelines().catch(console.error);
  }, []);

  // websocket connection for real-time pipeline updates
  useEffect(() => {
    if (!user?.id) {
      return;
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const baseWsUrl = baseUrl.replace('http', 'ws').replace('https', 'wss');
    const wsUrl = `${baseWsUrl}/users/${user.id}/video-pipelines/ws`;
    let socket: WebSocket | null = null;
    let isCleaningUp = false;

    try {
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        if (!isCleaningUp) {
          console.log("connected to user pipeline state socket");
        }
      };

      socket.onmessage = (event) => {
        if (!isCleaningUp) {
          try {
            const data = JSON.parse(event.data);
            console.log("received pipeline update:", data);
            fetchVideoPipelines().catch(console.error);
          } catch (error) {
            console.error("Error parsing WebSocket message:", error);
          }
        }
      };

      socket.onerror = (error) => {
        // only log errors if not cleaning up (to avoid noise from React Strict Mode)
        if (!isCleaningUp && socket?.readyState !== WebSocket.CLOSING && socket?.readyState !== WebSocket.CLOSED) {
          console.error("websocket error:", error);
        }
      };

      socket.onclose = (event) => {
        // only log if it wasn't a normal closure during cleanup
        if (!isCleaningUp && event.code !== 1000) {
          console.log("websocket closed:", event.code, event.reason);
        }
      };
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
    }

    // cleanup function to close the websocket connection when the component unmounts
    return () => {
      isCleaningUp = true;
      if (socket) {
        try {
          if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
            socket.close(1000, 'Component unmounting');
          }
        } catch (error) {
          // ignore errors during cleanup
        }
      }
    };
  }, [user?.id]);

  // check for create query parameter and open modal
  useEffect(() => {
    const createParam = searchParams.get("create");
    if (createParam === "true") {
      setIsModalOpen(true);
      // remove the query parameter from url without reloading
      router.replace("/video-pipelines", { scroll: false });
    }
  }, [searchParams, router]);

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      {/* header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
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
          {videoPipelines.length > 0 ? (
            <VideoPipelineTable videoPipelines={videoPipelines as VideoPipelineTableItem[]} 
              onDelete={handleDeleteVideoPipeline}
            />
          ) : (
            <div className="flex min-h-[60vh] w-full items-center justify-center">
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
        onCreateTask={handleCreateVideoPipeline}
      />
    </div>
  );
}