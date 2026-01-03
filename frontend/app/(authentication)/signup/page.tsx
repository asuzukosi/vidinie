"use client";

import { SignupForm } from "@/components/authentication/SignUpForm";
import client from "@/lib/sdk/client";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { useDispatch } from "react-redux";
import { setUser } from "@/lib/store/slices/userSlice";

export default function SignUpPage() {
  const router = useRouter();
  const dispatch = useDispatch();

  const handleSignup = async (name: string, email: string, password: string) => {
    try {
      await client.register(name, email, password);
      toast.success("Account created successfully!");
      
      // auto-login after signup
      const response = await client.login(email, password);
      const userData = {
        id: response.id,
        name: response.username,
        email: response.email,
        token: response.token,
        created_at: response.created_at,
        updated_at: response.updated_at,
        is_verified: response.is_verified,
        current_subscription: response.current_subscription,
        profile_picture: response.profile_picture,
        stripe_customer_id: response.stripe_customer_id,
      };
      dispatch(setUser(userData));
      // sync token to sdk client
      client.setToken(response.token);
      
      router.push("/tasks");
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