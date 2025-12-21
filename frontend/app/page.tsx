"use client";

import Sidebar from "@/components/sidebar/Sidebar";
import { PipelineStagesManager } from "@/components/PipelineStagesManager";
import { VideoPlayer } from "@/components/VideoPlayer";
import CreatePipelineForm from "@/components/forms/create-pipeline/CreatePipelineForm";
import { FormTabs } from "@/components/forms/create-pipeline/FormTabs";
import TableMain from "@/components/TableMain";
import { UnderConstruction } from "@/components/UnderConstruction";
export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
        <Sidebar>
            {/* <VideoPlayer pipelineId="123" /> */}
            {/* <FormTabs />
            <CreatePipelineForm />
            <TableMain /> */}
            <UnderConstruction />
        </Sidebar>
    </div>
  );
}
