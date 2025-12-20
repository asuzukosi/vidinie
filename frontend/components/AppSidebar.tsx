"use client";

import { Sidebar, SidebarContent } from "@/components/ui/sidebar";
import {
  IconAd2,
  IconBellRinging,
  IconCalendar,
  IconCalendarStats,
  IconListDetails,
  IconNews,
  IconNotebook,
  IconProgressCheck,
  IconSettingsCode,
} from "@tabler/icons-react";
import { LayoutDashboard, Package } from "lucide-react";
import { NavCollapsible } from "./NavCollapsible";
import { NavFooter } from "./NavFooter";
import { NavHeader } from "./NavHeader";
import { NavMain } from "./NavMain";
import type { SidebarData } from "./types";
import { useSession } from "@/lib/auth-client";

const navMain = [
  {
    id: "overview",
    title: "Overview",
    url: "/overview",
    icon: LayoutDashboard,
    isActive: true,
  },
  {
    id: "tasks",
    title: "Tasks",
    url: "/tasks",
    icon: IconListDetails,
  },
  {
    id: "completed",
    title: "Completed",
    url: "/completed",
    icon: IconProgressCheck,
  },
  {
    id: "notifications",
    title: "Notifications",
    url: "/notifications",
    icon: IconBellRinging,
  },
];

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { data: session } = useSession();

  const user = {
    name: session?.user?.name || "Guest",
    email: session?.user?.email || "",
    avatar: session?.user?.image || "",
  };

  const data: SidebarData = {
    user,
    navMain,
  };

  return (
    <Sidebar {...props}>
      <NavHeader data={data} />
      <SidebarContent>
        <NavMain items={data.navMain} />
      </SidebarContent>
      <NavFooter user={user} />
    </Sidebar>
  );
}
