"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { SignupForm } from "@/components/SignUpForm";
import { authClient } from "@/lib/auth-client";

export default function SignUpPage() {
  const router = useRouter();
  const { data: session, isPending } = authClient.useSession();

  useEffect(() => {
    if (!isPending && session) {
      router.replace("/overview");
    }
  }, [isPending, router, session]);

  const handleSignup = async (name: string, email: string, password: string) => {
    const { error } = await authClient.signUp.email({
      name,
      email,
      password,
      callbackURL: "/overview",
    });

    if (error) {
      toast.error(error.message || "Signup failed.");
      return;
    }

    router.push("/overview");
    router.refresh();
  };

  const handleGoogleSignup = async () => {
    const { error } = await authClient.signIn.social({
      provider: "google",
      callbackURL: "/overview",
    });

    if (error) {
      toast.error(error.message || "Google signup failed.");
    }
  };

  if (!isPending && session) {
    return null;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 px-4 dark:bg-black">
      <SignupForm onSignup={handleSignup} onGoogleSignup={handleGoogleSignup} />
    </div>
  );
}
