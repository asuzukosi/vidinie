"use client";
import { Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { LoginForm } from "@/components/LoginForm";
import { authClient } from "@/lib/auth-client";
import { toast } from "sonner";

function SignInContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const callbackUrl = searchParams.get("callbackUrl") || "/";

  const handleLogin = async (email: string, password: string) => {
    const { data, error } = await authClient.signIn.email({
      email,
      password,
    });
    if (error) {
      console.error("Login error:", error);
      toast.error("Login failed", {
        description: error.message || "Invalid email or password. Please try again.",
      });
      return;
    }
    toast.success("Login successful", {
      description: "Welcome back!",
    });
    router.push(callbackUrl);
  };
  const handleGoogleLogin = async () => {
    await authClient.signIn.social({
      provider: "google",
    });
  };

  return (
    <div className="flex min-h-svh w-full items-center justify-center p-6 md:p-10">
      <div className="w-full max-w-sm">
        <LoginForm onLogin={handleLogin} onGoogleLogin={handleGoogleLogin} />
      </div>
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={
      <div className="flex min-h-svh w-full items-center justify-center p-6 md:p-10">
        <div className="w-full max-w-sm">Loading...</div>
      </div>
    }>
      <SignInContent />
    </Suspense>
  );
}
