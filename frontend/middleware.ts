import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';

const isPublicRoute = createRouteMatcher([
  "/",
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/api/webhooks/(.*)",
]);

export default clerkMiddleware(async (auth, request) => {
  // protect all routes except public routes
  if (!isPublicRoute(request)) {
    const session = await auth();
    if (!session || !session.userId) {
      // not authenticated, redirect to sign-in page or return 401
      return Response.redirect('/sign-in');
    }
  }
});


export const config = {
  matcher: [
    // skip next.js internals and static files
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // always run for api routes
    '/(api|trpc)(.*)',
  ],
};