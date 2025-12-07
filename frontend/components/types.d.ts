import type { ElementType } from "react";

export interface NavItem {
  id: string;
  title: string;
  icon: ElementType;
  url?: string;
  isActive?: boolean;
}

export interface User {
  name: string;
  email: string;
  avatar: string;
}

export interface TagItem {
  id: string;
  title: string;
  href: string;
  color: string;
}

export interface TeamItem {
  id: string;
  title: string;
  icon: ElementType;
}

export interface ProjectItem {
  id: string;
  title: string;
  icon: ElementType;
}

export interface SidebarData {
  user: User;
  navMain: NavItem[];
  navCollapsible: {
    tags: TagItem[];
    teams: TeamItem[];
    projects: ProjectItem[];
  };
}
