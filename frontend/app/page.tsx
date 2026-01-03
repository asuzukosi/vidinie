"use client";
import Sidebar from "@/components/sidebar/Sidebar";
// import { PipelineStagesManager } from "@/components/VideoPipelineStagesManager";
// import { VideoPlayer } from "@/components/VideoPlayer";
// import CreatePipelineForm from "@/components/forms/create-pipeline/CreateVideoPipelineForm";
// import { FormTabs } from "@/components/forms/create-pipeline/FormTabs";
// import TableMain from "@/components/TableMain";
// import { UnderConstruction } from "@/components/UnderConstruction";
import { LoadingPage } from "@/components/utils/LoadingPage";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
export default function Home() {
  const router = useRouter();
  useEffect(() => {
    router.push("/video-pipelines");
  }, [router]);
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
        <Sidebar>
            {/* <VideoPlayer videoPipelineId="123" /> */}
            {/* <FormTabs />
            <CreateVideoPipelineForm />
            <TableMain /> */}
            {/* <UnderConstruction /> */}
            <LoadingPage />
        </Sidebar>
    </div>
  );
}
