"use client";

import { useEffect, useState, useRef } from "react";
import { useSession, getSession, signOut } from "@/lib/auth-client";
import { useDispatch } from "react-redux";
import { clearUser } from "@/lib/store/slices/auth-slice";
import { LoadingPage } from "./loading-page";

export function AuthLoader({ children }: { children: React.ReactNode }) {
  const { isPending } = useSession();
  const dispatch = useDispatch();
  const [isValidating, setIsValidating] = useState(true);
  const hasValidated = useRef(false);

  useEffect(() => {
    if (hasValidated.current || isPending) {
      return;
    }

    const logoutAndClearUser = async () => {
      dispatch(clearUser());
      await signOut().catch((error) => {
        console.error("Error during sign out:", error);
      });
    };

    const validateSession = async () => {
      hasValidated.current = true;
      
      const sessionResult = await getSession().catch((error) => {
        console.error("Error validating session:", error);
        return null;
      });

      const hasValidSession = sessionResult?.data?.session && sessionResult?.data?.user;
      
      if (!hasValidSession) {
        console.log("Session validation failed - logging out and clearing user data");
        await logoutAndClearUser();
      }
      
      setIsValidating(false);
    };

    validateSession();
  }, [isPending, dispatch]);

  if (isPending || isValidating) {
    return <LoadingPage />;
  }

  return <>{children}</>;
}

