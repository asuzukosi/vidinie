"use client";

import { LoginForm } from "@/components/authentication/LoginForm";
import client from "@/lib/sdk/client";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { useDispatch, useSelector } from "react-redux";
import { setUser } from "@/lib/store/slices/authSlice";
import { useEffect } from "react";
import type { RootState } from "@/lib/store/store";

export default function SignInPage() {
  const router = useRouter();
  const dispatch = useDispatch();
  const user = useSelector((state: RootState) => state.auth.user);

  useEffect(() => {
    // check if user is already authenticated
    if (user?.token) {
      router.push("/video-pipelines");
      return;
    }
  }, [user, router]);

  const handleLogin = async (email: string, password: string) => {
    try {
      const response = await client.login(email, password);
      // store all user data and token in redux
      const userData = {
        id: response.id,
        email: response.email,
        token: response.token,
        created_at: response.created_at,
        updated_at: response.updated_at,
        is_verified: response.is_verified,
      };
      dispatch(setUser(userData));
      // sync token to sdk client
      client.setToken(response.token);
      toast.success("Login successful!");
      router.push("/video-pipelines");
    } catch (error: any) {
      toast.error("Login failed", {
        description: error.message || "Invalid email or password",
      });
      throw error;
    }
  };

  const handleGoogleLogin = async () => {
    toast.info("Google login coming soon");
  };

  const handleForgotPassword = async () => {
    toast.info("Forgot password coming soon");
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-zinc-50 dark:bg-black p-4">
      <div className="w-full max-w-md">
        <LoginForm onLogin={handleLogin} onGoogleLogin={handleGoogleLogin} onForgotPassword={handleForgotPassword} />
      </div>
    </div>
  );
}