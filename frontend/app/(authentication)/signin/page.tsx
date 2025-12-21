"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { LoginForm } from "@/components/authentication/LoginForm";
import { authClient } from "@/lib/auth-client";

export default function SignInPage() {
  const router = useRouter();
  const { data: session, isPending } = authClient.useSession();

  useEffect(() => {
    if (!isPending && session) {
      router.replace("/overview");
    }
  }, [isPending, router, session]);

  const handleLogin = async (email: string, password: string) => {
    const { error } = await authClient.signIn.email({
      email,
      password,
      callbackURL: "/overview",
    });

    if (error) {
      toast.error(error.message || "Login failed.");
      return;
    }

    router.push("/overview");
    router.refresh();
  };

  const handleGoogleLogin = async () => {
    const { error } = await authClient.signIn.social({
      provider: "google",
      callbackURL: "/overview",
    });

    if (error) {
      toast.error(error.message || "Google login failed.");
    }
  };

  if (!isPending && session) {
    return null;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 px-4 dark:bg-black">
      <LoginForm onLogin={handleLogin} onGoogleLogin={handleGoogleLogin} />
    </div>
  );
}
