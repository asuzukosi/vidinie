'use client';
import { useSession } from "@/lib/auth-client";
import { redirect } from "next/navigation";

export default function ProtectedScreen({ children }: { children: React.ReactNode }) {
    const { data: session, isPending } = useSession();

    if (isPending) {
        return null;
    }

    if (!session) {
        redirect("/sign-in");
    }

    return (
        <>
        {children}
        </>
    );
}
