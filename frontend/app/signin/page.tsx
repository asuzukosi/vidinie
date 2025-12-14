"use client";
import { LoginForm } from "@/components/login-form";
import { authClient } from "@/lib/auth-client";
export default function Page() {
  const handleLogin = async (email: string, password: string) => {
    const { data, error } = await authClient.signIn.email({
      email,
      password,
      callbackURL: "/",
    });
    if (error) {
      console.error("Login error:", error);
    }
  };
  return (
    <div className="flex min-h-svh w-full items-center justify-center p-6 md:p-10">
      <div className="w-full max-w-sm">
        <LoginForm onLogin={handleLogin} />
      </div>
    </div>
  );
}
