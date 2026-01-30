import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { StoreProvider } from "@/lib/store/components/store-provider";
import { Toaster } from "@/components/ui/sonner";
import GoogleAnalytics from "@/components/utils/google-analytics";
import { AuthLoader } from "@/components/utils/auth-loader";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "vidinie.",
  description: "Create professional explainer videos from your content",
  icons: {
    icon: "/vidinie.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <GoogleAnalytics />
        <StoreProvider>
          <AuthLoader>{children}</AuthLoader>
        </StoreProvider>
        <Toaster />
      </body>
    </html>
  );
}
