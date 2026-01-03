"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useSelector } from "react-redux";
import Sidebar from "@/components/sidebar/Sidebar";
import client from "@/lib/sdk/client";
import type { RootState } from "@/lib/store/store";
import { LoadingPage } from "@/components/utils/LoadingPage";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const user = useSelector((state: RootState) => state.auth.user);
    const [isCheckingAuth, setIsCheckingAuth] = useState(true);

    useEffect(() => {
        checkAuthentication();
    }, [user]);

    const checkAuthentication = () => {
        // first check redux state
        if (user?.token) {
            // sync token to sdk client
            client.setToken(user.token);
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