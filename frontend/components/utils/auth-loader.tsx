"use client";

import { useSession } from "@/lib/auth-client";
import { LoadingPage } from "./loading-page";

export function AuthLoader({ children }: { children: React.ReactNode }) {
  const { isPending } = useSession();

  // show loading page while checking authentication status
  if (isPending) {
    return <LoadingPage />;
  }

  // render children once auth status is determined
  return <>{children}</>;
}

