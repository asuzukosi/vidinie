"use client";

import { useSelector } from "react-redux";
import { Sidebar, SidebarContent } from "@/components/ui/sidebar";
import {
  IconSettings,
  IconUser,
  IconListDetails,
} from "@tabler/icons-react";
import { NavFooter } from "@/components/sidebar/nav-footer";
import { NavHeader } from "@/components/sidebar/nav-header";
import { NavMain } from "@/components/sidebar/nav-main";
import type { NavItem } from "@/lib/types";
import type { RootState } from "@/lib/store/store";
import client from "@/lib/sdk/client";

const navItems: NavItem[] = [
    {
      id: "video-pipelines",
      title: "Videos",
      url: "/video-pipelines",
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
  const user = useSelector((state: RootState) => state.auth.user);
  
  // get avatar url from profile picture, or use fallback
  const getAvatarUrl = () => {
    if (user?.profile_picture) {
      return client.getProfilePictureUrl(user.profile_picture);
    }
    // fallback to ui-avatars if no profile picture
    if (user?.email) {
      return `https://ui-avatars.com/api/?name=${encodeURIComponent(user.email)}&background=random`;
    }
    return null;
  };

  const userData = user ? {
    email: user.email,
    avatar: getAvatarUrl() || null,
  } : {
    email: "unknown@user.com",
    avatar: null,
  };

  return (
    <Sidebar {...props}>
      <NavHeader navItems={navItems} />
      <SidebarContent>
        <NavMain items={navItems} />
      </SidebarContent>
      <NavFooter user={userData} />
    </Sidebar>
  );
}

