"use client";

import { LoginForm } from "@/components/authentication/LoginForm";
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

  const handleGoogleLogin = useCallback(async () => {
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
          script.onload = () => {
            // Wait a bit for Google to fully initialize
            setTimeout(() => {
              if (window.google?.accounts?.id) {
                resolve(undefined);
              } else {
                reject(new Error("Google Sign-In services failed to initialize. Please disable ad blockers or privacy extensions and try again."));
              }
            }, 500);
          };
          script.onerror = () => {
            reject(new Error("Failed to load Google Sign-In. Please check if ad blockers are enabled and try disabling them."));
          };
          setTimeout(() => {
            reject(new Error("Google Sign-In script timed out. Please check your internet connection or disable ad blockers."));
          }, 10000); // 10 second timeout
        });
      }

      // check if Google services are available
      if (!window.google?.accounts?.id) {
        throw new Error("Google Sign-In services are not available. Please disable ad blockers or privacy extensions and try again.");
      }

      // use a promise-based approach to handle the callback
      let callbackResolve: ((value: any) => void) | null = null;
      let callbackReject: ((error: Error) => void) | null = null;

      const callbackPromise = new Promise<any>((resolve, reject) => {
        callbackResolve = resolve;
        callbackReject = reject;
      });

      // initialize google identity services with callback
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: (response: any) => {
          if (response.credential && callbackResolve) {
            callbackResolve(response);
          } else if (callbackReject) {
            callbackReject(new Error("No credential received from Google"));
          }
        },
        use_fedcm_for_prompt: true,
      });

      // Create a temporary container for the Google button
      const buttonContainer = document.createElement('div');
      buttonContainer.id = 'google-signin-button-temp';
      buttonContainer.style.position = 'fixed';
      buttonContainer.style.left = '-9999px';
      buttonContainer.style.top = '-9999px';
      document.body.appendChild(buttonContainer);

      // Render the Google Sign-In button
      try {
        window.google.accounts.id.renderButton(buttonContainer, {
          type: 'standard',
          theme: 'outline',
          size: 'large',
          text: 'signin_with',
          width: 300,
        });

        // Wait a moment for the button to render, then click it
        setTimeout(() => {
          const googleButton = buttonContainer.querySelector('div[role="button"]') as HTMLElement;
          if (googleButton) {
            googleButton.click();
          } else {
            // Fallback: try prompt if button rendering failed
            try {
              window.google?.accounts.id.prompt();
            } catch (promptError) {
              document.body.removeChild(buttonContainer);
              if (callbackReject) {
                callbackReject(new Error("Unable to start Google Sign-In. Please try disabling ad blockers."));
              }
              return;
            }
          }
        }, 200);
      } catch (renderError) {
        document.body.removeChild(buttonContainer);
        // Fallback: try prompt
        try {
          window.google?.accounts.id.prompt();
        } catch (promptError) {
          throw new Error("Unable to start Google Sign-In. Please try disabling ad blockers.");
        }
      }

      // Wait for the callback with a timeout
      const timeoutId = setTimeout(() => {
        document.body.removeChild(buttonContainer);
        if (callbackReject) {
          callbackReject(new Error("Google Sign-In timed out. Please try again."));
        }
      }, 60000); // 60 second timeout

      try {
        const response = await callbackPromise;
        clearTimeout(timeoutId);
        document.body.removeChild(buttonContainer);

        if (!response.credential) {
          toast.error("Google authentication failed", {
            description: "No credential received from Google",
          });
          return;
        }

        // send id token to api route which verifies and handles authentication
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
        toast.success("Login successful!");
        router.push("/video-pipelines");
      } catch (callbackError: any) {
        clearTimeout(timeoutId);
        if (buttonContainer.parentNode) {
          document.body.removeChild(buttonContainer);
        }
        throw callbackError;
      }
    } catch (error: any) {
      const errorMessage = error.message || "Please try again";
      toast.error("Failed to initialize Google Sign-In", {
        description: errorMessage.includes("ad blocker") || errorMessage.includes("privacy")
          ? errorMessage
          : `${errorMessage}. If the issue persists, please try disabling ad blockers or privacy extensions.`,
        duration: 6000,
      });
    }
  }, [dispatch, router]);

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