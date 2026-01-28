"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarFooter,
  SidebarMenu,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { getInitials } from "@/lib/utils";

import {
  LogOut,
  Settings,
  User,
} from "lucide-react";
import { authClient } from "@/lib/auth-client";
import { useDispatch } from "react-redux";
import { clearUser } from "@/lib/store/slices/auth-slice";

export function NavFooter({
  user,
}: {
  user: {
    email: string;
    avatar?: string | null;
  };
}) {
  const router = useRouter();
  const dispatch = useDispatch();
  

  const handleLogout = async () => {
    dispatch(clearUser());
    await authClient.signOut();
    router.push("/signin");
  };

  return (
    <SidebarFooter className="p-4">
      <SidebarMenu>
        <SidebarMenuItem>
          <div className="flex items-center gap-2 justify-between">
            <div className="flex items-center gap-2">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Avatar className="h-8 w-8 rounded-full">
                    {user.avatar && (
                      <AvatarImage src={user.avatar} alt={user.email} />
                    )}
                    <AvatarFallback className="rounded-full">
                      {getInitials(user.email)}
                    </AvatarFallback>
                  </Avatar>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="m-2">
                  <DropdownMenuItem asChild>
                    <Link href="/profile" className="flex items-center">
                      <User size={16} className="opacity-80 mr-2" aria-hidden="true" />
                      Profile
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/settings" className="flex items-center">
                      <Settings
                        size={16}
                        className="opacity-80 mr-2"
                        aria-hidden="true"
                      />
                      Settings
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={handleLogout}>
                    <LogOut size={16} className="opacity-80 mr-2" aria-hidden="true" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

            </div>
            <DropdownMenu>
              {/* <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="rounded-full">
                  <PlusCircle size={16} />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="m-2">
                <DropdownMenuLabel>New</DropdownMenuLabel>
                <DropdownMenuItem asChild>
                  <Link href="/new-project" className="flex items-center">
                    <Plus size={16} className="opacity-80 mr-2" aria-hidden="true" />
                    Project
                  </Link>
                </DropdownMenuItem>
              </DropdownMenuContent> */}
            </DropdownMenu>
          </div>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarFooter>
  );
}

