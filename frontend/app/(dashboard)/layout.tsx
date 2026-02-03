"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useSelector, useDispatch } from "react-redux";
import { authClient } from "@/lib/auth-client";
import { setUser } from "@/lib/store/slices/auth-slice";
import { Sidebar } from "@/components/sidebar/root-sidebar";
import type { RootState } from "@/lib/store/store";
import { LoadingPage } from "@/components/utils/loading-page";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const dispatch = useDispatch();
    const user = useSelector((state: RootState) => state.auth.user);
    const [isCheckingAuth, setIsCheckingAuth] = useState(true);

    useEffect(() => {
        checkAuthentication();
    }, [user]);

    const checkAuthentication = async () => {
        // if no user in redux store, try to sync from better-auth session
        // this handles oauth callbacks where user is redirected before redux is populated
        if (!user) {
            try {
                const session = await authClient.getSession();
                if (session?.data?.user) {
                    // Sync session to Redux
                    const userData = {
                        id: session.data.user.id,
                        email: session.data.user.email,
                        token: session.data.session?.token || "",
                        created_at: session.data.user.createdAt.toISOString(),
                        updated_at: session.data.user.updatedAt.toISOString(),
                        is_verified: session.data.user.emailVerified || false,
                    };
                    dispatch(setUser(userData));
                    setIsCheckingAuth(false);
                    return;
                }
            } catch (error) {
                console.error("Error syncing session:", error);
            }
            // if no session found, redirect to signin
            setIsCheckingAuth(false);
            router.push("/signin");
            return;
        }
        
        // user data exists in redux store, proceed normally
        setIsCheckingAuth(false);
    };

    // show loading page during auth check or if no user (redirect in progress)
    if (isCheckingAuth) {
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