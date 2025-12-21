"use client";

import { Sidebar, SidebarContent } from "@/components/ui/sidebar";
import {
  IconBellRinging,
  IconListDetails,
  IconProgressCheck,
} from "@tabler/icons-react";
import { LayoutDashboard } from "lucide-react";
import { NavCollapsible } from "./NavCollapsible";
import { NavFooter } from "./NavFooter";
import { NavHeader } from "./NavHeader";
import { NavMain } from "./NavMain";
import type { SidebarData } from "./types";

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
  const user = {
    name: "Guest",
    email: "",
    avatar: "",
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
