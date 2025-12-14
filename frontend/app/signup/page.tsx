"use client";
import { SignupForm } from "@/components/signup-form";
import { authClient } from "@/lib/auth-client";

export default function SignupPage() {
  const handleSignup = async (
    name: string,
    email: string,
    password: string,
  ) => {
    const { data, error } = await authClient.signUp.email({
      name,
      email,
      password,
      callbackURL: "/",
    });

    if (error) {
      alert(error.message);
    }
  };

  return (
    <div className="flex min-h-svh w-full items-center justify-center p-6 md:p-10">
      <div className="w-full max-w-sm">
        <SignupForm onSignup={handleSignup} />
      </div>
    </div>
  );
}
