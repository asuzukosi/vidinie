'use client';
import { useUser } from "@clerk/nextjs";
import { redirect } from "next/navigation";

export default function ProtectedScreen({ children }: { children: React.ReactNode }) {
    const { isSignedIn } = useUser();
    if (!isSignedIn) {
        redirect("/sign-in");
    }
    return (
        <>
        {children}
        </>
    );
}
