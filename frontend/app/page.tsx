"use client";
import Sidebar from "@/components/sidebar/Sidebar";
//  dimport { PipelineStagesManager } from "@/components/PipelineStagesManager";
// import { VideoPlayer } from "@/components/VideoPlayer";
// import CreatePipelineForm from "@/components/forms/create-pipeline/CreatePipelineForm";
// import { FormTabs } from "@/components/forms/create-pipeline/FormTabs";
// import TableMain from "@/components/TableMain";
// import { UnderConstruction } from "@/components/UnderConstruction";
import { LoadingPage } from "@/components/LoadingPage";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
export default function Home() {
  const router = useRouter();
  useEffect(() => {
    router.push("/overview");
  }, [router]);
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
        <Sidebar>
            {/* <VideoPlayer pipelineId="123" /> */}
            {/* <FormTabs />
            <CreatePipelineForm />
            <TableMain /> */}
            {/* <UnderConstruction /> */}
            <LoadingPage />
        </Sidebar>
    </div>
  );
}
