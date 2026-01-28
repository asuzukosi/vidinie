"use client";

import { SignupForm } from "@/components/authentication/sign-up-form";
import { authClient } from "@/lib/auth-client";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { useDispatch } from "react-redux";
import { setUser } from "@/lib/store/slices/auth-slice";
import { useEffect, useCallback } from "react";

export default function SignUpPage() {
  // router to navigate to the video pipelines page
  const router = useRouter();
  // dispatch to dispatch the user data to the redux store
  const dispatch = useDispatch();

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
      toast.success("Account created successfully!");
      // auto-login after signup
      const loginResponse = await authClient.signIn.email({
        email,
        password,
      });
      // if there is an error, throw an error
      if (loginResponse.error) {
        throw new Error(loginResponse.error.message || "Login failed after signup");
      }
      // get session to store user data
      const session = await authClient.getSession();
      if (session?.data && session.data.user) {
        // store user data in redux store
        const userData = { id: session.data.user.id, email: session.data.user.email, token: session.data.session?.token || "", created_at: session.data.user.createdAt.toISOString(), 
                           updated_at: session.data.user.updatedAt.toISOString(), is_verified: session.data.user.emailVerified || false };
        // dispatch user data to redux store
        dispatch(setUser(userData));
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
        callbackURL: "/video-pipelines",
      });
      // if there is an error, throw an error
      if (response.error) {
        throw new Error(response.error.message || "Google authentication failed");
      }
      // get session after google authentication
      const session = await authClient.getSession();
      if (session?.data && session.data.user) {
        // store user data in redux store
        const userData = { id: session.data.user.id, email: session.data.user.email, token: session.data.session?.token || "", created_at: session.data.user.createdAt.toISOString(), 
                           updated_at: session.data.user.updatedAt.toISOString(), is_verified: session.data.user.emailVerified || false };
        // dispatch user data to redux store
        dispatch(setUser(userData));
      }
      // show success toast
      toast.success("Account created successfully!");
      router.push("/video-pipelines");
    } catch (error: any) {
      toast.error("Google authentication failed", {
        description: error.message || "Please try again",
      });
    }
  }, [dispatch, router]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-zinc-50 dark:bg-black p-4">
      <div className="w-full max-w-md">
        <SignupForm onSignup={handleSignup} onGoogleSignup={handleGoogleSignup} />
      </div>
    </div>
  );
}