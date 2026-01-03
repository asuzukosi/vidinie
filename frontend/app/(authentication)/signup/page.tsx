"use client";

import { SignupForm } from "@/components/authentication/SignUpForm";
import client from "@/lib/sdk/client";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { useDispatch, useSelector } from "react-redux";
import { setUser } from "@/lib/store/slices/authSlice";
import { useEffect } from "react";
import type { RootState } from "@/lib/store/store";

export default function SignUpPage() {
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

  const handleSignup = async (username: string, email: string, password: string) => {
    try {
      await client.register(username, email, password);
      toast.success("Account created successfully!");
      
      // auto-login after signup
      const response = await client.login(email, password);
      const userData = {
        id: response.id,
        username: response.username,
        email: response.email,
        token: response.token,
        created_at: response.created_at,
        updated_at: response.updated_at,
        is_verified: response.is_verified,
      };
      dispatch(setUser(userData));
      // sync token to sdk client
      client.setToken(response.token);
      
      router.push("/video-pipelines");
    } catch (error: any) {
      toast.error("Signup failed", {
        description: error.message || "Could not create account",
      });
      throw error;
    }
  };

  const handleGoogleSignup = async () => {
    toast.info("Google signup coming soon");
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-zinc-50 dark:bg-black p-4">
      <div className="w-full max-w-md">
        <SignupForm onSignup={handleSignup} onGoogleSignup={handleGoogleSignup} />
      </div>
    </div>
  );
}