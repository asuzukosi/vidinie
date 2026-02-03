"use client";

import { SignupForm } from "@/components/authentication/sign-up-form";
import { authClient } from "@/lib/auth-client";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { useEffect, useCallback } from "react";

export default function SignUpPage() {
  // router to navigate to the video pipelines page
  const router = useRouter();

  useEffect(() => {
    // check if user is already authenticated via better-auth session
    authClient.getSession().then((session) => {
      if (session?.data && session.data.user) {
        // navigate to the video pipelines page
        router.push("/video-pipelines");
      }
      // if user is not authenticated, continue to the signup page
    });
  }, [router]);

  const handleSignup = async (email: string, password: string) => {
    try {
      const result = await authClient.signUp.email({ name: email, email, password });
      // if there is an error, throw an error
      if (result.error) {
        throw new Error(result.error.message || "Could not create account");
      }
      // auto-login after signup
      const loginResponse = await authClient.signIn.email({
        email,
        password,
      });
      // if there is an error, throw an error
      if (loginResponse.error) {
        throw new Error(loginResponse.error.message || "Login failed after signup");
      }
      // show success toast
      toast.success("Account created successfully!");
      // navigate to the video pipelines page
      router.push("/video-pipelines");
    } catch (error: any) {
      toast.error("Signup failed", {
        description: error.message || "Could not create account",
      });
      throw error;
    }
  };

  const handleGoogleSignup = useCallback(async () => {
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
      toast.success("Account created successfully!");
      router.push("/");
    } catch (error: any) {
      toast.error("Google authentication failed", {
        description: error.message || "Please try again",
      });
    }
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-zinc-50 dark:bg-black p-4">
      <div className="w-full max-w-md">
        <SignupForm onSignup={handleSignup} onGoogleSignup={handleGoogleSignup} />
      </div>
    </div>
  );
}