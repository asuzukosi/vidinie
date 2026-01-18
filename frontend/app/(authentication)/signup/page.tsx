"use client";

import { SignupForm } from "@/components/authentication/SignUpForm";
import client from "@/lib/sdk/client";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { useDispatch, useSelector } from "react-redux";
import { setUser } from "@/lib/store/slices/authSlice";
import { useEffect, useCallback } from "react";
import type { RootState } from "@/lib/store/store";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: any) => void;
          prompt: () => void;
          renderButton: (element: HTMLElement, config: any) => void;
        };
      };
    };
  }
}

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

  const handleSignup = async (email: string, password: string) => {
    try {
      await client.register(email, password);
      toast.success("Account created successfully!");
      
      // auto-login after signup
      const response = await client.login(email, password);
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
      const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID;
      if (!googleClientId) {
        toast.error("google authentication not configured");
        return;
      }

      // load google identity services script if not already loaded
      if (!window.google) {
        const script = document.createElement("script");
        script.src = "https://accounts.google.com/gsi/client";
        script.async = true;
        script.defer = true;
        document.head.appendChild(script);

        await new Promise((resolve, reject) => {
          script.onload = resolve;
          script.onerror = reject;
          setTimeout(reject, 10000); // 10 second timeout
        });
      }

      // initialize google identity services
      window.google?.accounts.id.initialize({
        client_id: googleClientId,
        callback: async (response: any) => {
          try {
            if (!response.credential) {
              toast.error("google authentication failed");
              return;
            }

            // send id token to  api route which verifies and handles authentication
            const apiResponse = await fetch('/api/auth/google', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ id_token: response.credential }),
            });

            if (!apiResponse.ok) {
              const errorData = await apiResponse.json().catch(() => ({}));
              throw new Error(errorData.error || 'Authentication failed');
            }

            const loginResponse = await apiResponse.json();
            
            // store user data and token in redux
            const userData = {
              id: loginResponse.id,
              email: loginResponse.email,
              token: loginResponse.token,
              created_at: loginResponse.created_at,
              updated_at: loginResponse.updated_at,
              is_verified: loginResponse.is_verified,
            };
            dispatch(setUser(userData));
            client.setToken(loginResponse.token);
            toast.success("Account created successfully!");
            router.push("/video-pipelines");
          } catch (error: any) {
            toast.error("google signup failed", {
              description: error.message || "failed to authenticate with google",
            });
          }
        },
      });

      // trigger the google sign-in flow
      window.google?.accounts.id.prompt();
    } catch (error: any) {
      toast.error("failed to initialize google sign-in", {
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