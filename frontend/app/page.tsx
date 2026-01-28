"use client";
import Sidebar from "@/components/sidebar/sidebar";
import { LoadingPage } from "@/components/utils/loading-page";
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
            <LoadingPage />
        </Sidebar>
    </div>
  );
}
