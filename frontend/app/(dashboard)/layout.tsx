"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useSelector } from "react-redux";
import Sidebar from "@/components/sidebar/sidebar";
import type { RootState } from "@/lib/store/store";
import { LoadingPage } from "@/components/utils/loading-page";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const user = useSelector((state: RootState) => state.auth.user);
    const [isCheckingAuth, setIsCheckingAuth] = useState(true);

    useEffect(() => {
        checkAuthentication();
    }, [user]);

    const checkAuthentication = () => {
        // better-auth handles tokens automatically, no need to sync
        if (user) {
            setIsCheckingAuth(false);
            return;
        }
        setIsCheckingAuth(false);
        router.push("/signin");
    };

    // show loading page during auth check or if no user (redirect in progress)
    if (isCheckingAuth || !user) {
        return <LoadingPage />;
    }

    return (
        <div className="flex min-h-screen bg-zinc-50 font-sans dark:bg-black">
            <Sidebar>
                {children}
            </Sidebar>
        </div>
    );
}