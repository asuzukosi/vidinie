"use client";

import {
  SidebarGroup,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import type { NavItem } from "@/components/sidebar/types";
import Link from "next/link";

export function NavMain({ items }: { items: NavItem[] }) {
  return (
    <SidebarGroup>
      <SidebarMenu>
        {items.map((item) => {
          const Icon = item.icon;

          return (
            <SidebarMenuItem key={item.id}>
              {item.url ? (
                <SidebarMenuButton tooltip={item.title} asChild>
                  <Link href={item.url}>
                    {Icon && <Icon className="mr-2 h-4 w-4" />}
                    <span>{item.title}</span>
                  </Link>
                </SidebarMenuButton>
              ) : (
                <SidebarMenuButton tooltip={item.title}>
                  {Icon && <Icon className="mr-2 h-4 w-4" />}
                  <span>{item.title}</span>
                </SidebarMenuButton>
              )}
            </SidebarMenuItem>
          );
        })}
      </SidebarMenu>
    </SidebarGroup>
  );
}
