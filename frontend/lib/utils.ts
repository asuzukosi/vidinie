import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const getInitials = (name: string) => {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
};

export function capitalizeFirstChar(str: string): string {
  // capitalize the first character of the string
  if (!str) return str;
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export function getLinkToImage(
  filePath: string | null | undefined,
  rootUrl: string = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  swap_with_media: boolean = true
): string {
  // handle empty, null, or undefined file paths
  if (!filePath || filePath.trim() === "") {
    return "";
  }
  
  let processedPath = filePath;
  if (swap_with_media) {
    processedPath = processedPath.replace("outputs", "media").replace("temp", "media");
  }
  // remove leading slash from path if present to avoid double slashes
  const cleanPath = processedPath.startsWith("/") ? processedPath.slice(1) : processedPath;
  // remove trailing slash from rootUrl if present
  const cleanRootUrl = rootUrl.endsWith("/") ? rootUrl.slice(0, -1) : rootUrl;
  return `${cleanRootUrl}/${cleanPath}`;
}

export function formatDate(dateString?: string): string {
  if (!dateString) return "N/A";
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  } catch {
    return dateString;
  }
}

// PostHog event types enum - all event names use dashes instead of underscores
export enum PostHogEvent {
  VIDEO_DOWNLOAD_REQUESTED_WITH_FREE_SUBSCRIPTION = "video-download-requested-with-free-subscription",
  VIDEO_DOWNLOAD_STARTED_WITH_PAID_SUBSCRIPTION = "video-download-started-with-paid-subscription",
  VIDEO_DOWNLOAD_COMPLETED = "video-download-completed",
  CHECKOUT_STARTED = "checkout-started",
  CHECKOUT_COMPLETED = "checkout-completed",
  CREATE_VIDEO_PIPELINE_CREATION_STARTED = "create-video-pipeline-creation-started",
  CREATE_VIDEO_PIPELINE_CREATION_COMPLETED = "create-video-pipeline-creation-completed",
  SHARE_VIDEO_PAGE_VIEWED = "share-video-page-viewed",
}
