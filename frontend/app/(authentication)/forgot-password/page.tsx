"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { authClient } from "@/lib/auth-client";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email) {
      toast.error("Email is required");
      return;
    }

    setIsLoading(true);
    try {
      // request password reset email using Better Auth
      const result = await (authClient as any).forgotPassword?.email?.({ email });
      
      if (result?.error) {
        // don't reveal if email exists for security - show generic success message
        // better-auth will handle this internally
        console.error("Password reset error:", result.error);
      }
      
      // always show success message for security
      setEmailSent(true);
      toast.success("If an account exists with this email, a password reset link has been sent.");
    } catch (error: any) {
      console.error("Error requesting password reset:", error);
      // still show success for security
      setEmailSent(true);
      toast.success("If an account exists with this email, a password reset link has been sent.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-zinc-50 dark:bg-black p-4">
      <div className="w-full max-w-md">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-center gap-2">
              <img src="/vidinie.png" alt="Logo" className="w-10 h-10 rounded-full" />
            </div>
            <CardTitle>Reset your password</CardTitle>
            <CardDescription>
              {emailSent
                ? "Check your email for a password reset link"
                : "Enter your email address and we'll send you a link to reset your password"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {emailSent ? (
              <FieldGroup>
                <Field>
                  <FieldDescription className="text-center">
                    We've sent a password reset link to <strong>{email}</strong> if an account exists with this email address.
                  </FieldDescription>
                </Field>
                <Field>
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full"
                    onClick={() => router.push("/signin")}
                  >
                    Back to Sign In
                  </Button>
                </Field>
              </FieldGroup>
            ) : (
              <form onSubmit={handleSubmit}>
                <FieldGroup>
                  <Field>
                    <FieldLabel htmlFor="email">Email</FieldLabel>
                    <Input
                      id="email"
                      type="email"
                      placeholder="m@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      disabled={isLoading}
                    />
                  </Field>
                  <Field>
                    <Button type="submit" disabled={isLoading} className="w-full">
                      {isLoading ? "Sending..." : "Send Reset Link"}
                    </Button>
                    <FieldDescription className="text-center">
                      Remember your password? <a href="/signin" className="underline">Sign in</a>
                    </FieldDescription>
                  </Field>
                </FieldGroup>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

