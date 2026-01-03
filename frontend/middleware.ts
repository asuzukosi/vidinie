import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// public routes that don't require authentication
const publicRoutes = [
  "/",
  "/signin",
  "/signup",
  "/api/webhooks",
];

function isPublicRoute(pathname: string): boolean {
  return publicRoutes.some(route => 
    pathname === route || pathname.startsWith(`${route}/`)
  );
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // allow public routes and api webhooks
  if (isPublicRoute(pathname)) {
    return NextResponse.next();
  }

  // otherwise, protected routes, authentication is handled client-side in the dashboard layout
  // the dashboard layout will check for tokens and redirect to login if needed
  return NextResponse.next();
}

export const config = {
  matcher: [
    // skip next.js internals and static files
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)|avatar-01\\.png).*)",
    // always run for api routes (except webhooks)
    "/(api|trpc)(.*)",
  ],
};
