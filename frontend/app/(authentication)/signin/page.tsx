"use client";

import { LoginForm } from "@/components/authentication/login-form";
import { authClient } from "@/lib/auth-client";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { useEffect, useCallback } from "react";

export default function SignInPage() {
  const router = useRouter();

  useEffect(() => {
    // check if user is already authenticated via better-auth session
    authClient.getSession().then((session) => {
      if (session?.data && session.data.user) {
        // navigate to the video pipelines page
        router.push("/video-pipelines");
      }
      // if user is not authenticated, continue to the login page
    });
  }, [router]);

  const handleLogin = async (email: string, password: string) => {
    try {
      // sign in with email and password
      const result = await authClient.signIn.email({ email, password });
      // if there is an error, throw an error
      if (result.error) {
        throw new Error(result.error.message || "Invalid email or password");
      }
      // show success toast
      toast.success("Login successful!");
      // navigate to the video pipelines page
      // router.push("/video-pipelines");
    } catch (error: any) {
      toast.error("Login failed", {
        description: error.message || "Invalid email or password",
      });
      throw error;
    }
  };

  const handleGoogleLogin = useCallback(async () => {
    try {
      // use better-auth google authentication
      const response = await authClient.signIn.social({
        provider: "google",
        callbackURL: "/",
      });
      // if there is an error, throw an error
      if (response.error) {
        throw new Error(response.error.message || "Google authentication failed");
      }
      toast.success("Login successful!");
      // router.push("/");
    } catch (error: any) {
      toast.error("Google authentication failed", {
        description: error.message || "Please try again",
      });
    }
  }, [router]);

  const handleForgotPassword = async () => {
    // navigate to forgot password page
    router.push("/forgot-password");
  };

  return (
    // login page container
    <div className="flex items-center justify-center min-h-screen bg-zinc-50 dark:bg-black p-4">
      <div className="w-full max-w-md">
        <LoginForm onLogin={handleLogin} onGoogleLogin={handleGoogleLogin} onForgotPassword={handleForgotPassword} />
      </div>
    </div>
  );
}