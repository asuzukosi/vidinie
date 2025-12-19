"use client";

import * as React from "react";

import { SidebarHeader } from "@/components/ui/sidebar";
import { SidebarData } from "./types";

interface NavHeaderProps {
  data: SidebarData;
}

export function NavHeader({ data }: NavHeaderProps) {
  return (
    <SidebarHeader className="px-2 pb-0 pt-3">
      {/* Header content can be added here if needed */}
    </SidebarHeader>
  );
}
