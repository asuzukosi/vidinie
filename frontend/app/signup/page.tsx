"use client";
import { useRouter } from "next/navigation";
import { SignupForm } from "@/components/signup-form";
import { authClient } from "@/lib/auth-client";
import { toast } from "sonner";

export default function SignupPage() {
  const router = useRouter();

  const handleSignup = async (
    name: string,
    email: string,
    password: string,
  ) => {
    const { data, error } = await authClient.signUp.email({
      name,
      email,
      password,
    });

    if (error) {
      toast.error("Signup failed", {
        description: error.message || "Unable to create account. Please try again.",
      });
      return;
    }
    toast.success("Account created successfully", {
      description: "Welcome to Vidinie!",
    });
    router.push("/");
  };

  return (
    <div className="flex min-h-svh w-full items-center justify-center p-6 md:p-10">
      <div className="w-full max-w-sm">
        <SignupForm onSignup={handleSignup} />
      </div>
    </div>
  );
}
