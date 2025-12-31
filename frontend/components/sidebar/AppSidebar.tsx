"use client";

import { Sidebar, SidebarContent } from "@/components/ui/sidebar";
import {
  IconSettings,
  IconUser,
  IconListDetails,
} from "@tabler/icons-react";
import { NavFooter } from "@/components/sidebar/NavFooter";
import { NavHeader } from "@/components/sidebar/NavHeader";
import { NavMain } from "@/components/sidebar/NavMain";
import type { User, NavItem } from "@/lib/types";

const user: User = {
  name: "Kosi Asuzu",
  email: "kosi@kosi.com",
  avatar: "https://ui-avatars.com/api/?name=Kosi Asuzu&background=random",
}

const navItems: NavItem[] = [
    {
      id: "tasks",
      title: "Tasks",
      url: "/tasks",
      icon: IconListDetails,
    },
    {
      id: "settings",
      title: "Settings",
      url: "/settings",
      icon: IconSettings,
    },
    {
      id: "profile",
      title: "Profile",
      url: "/profile",
      icon: IconUser,
    },
]

export function AppSidebar(props: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar {...props}>
      <NavHeader navItems={navItems} />
      <SidebarContent>
        <NavMain items={navItems} />
        {/* <NavCollapsible # TODO: add when needed
          favorites={data.navCollapsible.favorites}
          // teams={data.navCollapsible.teams}
          // topics={data.navCollapsible.topics}
        /> */}
      </SidebarContent>
      <NavFooter user={user} />
    </Sidebar>
  );
}
