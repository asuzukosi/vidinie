import SidebarLayout from "@/components/Sidebar";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex min-h-screen bg-zinc-50 font-sans dark:bg-black">
            <SidebarLayout>{children}</SidebarLayout>
        </div>
    );
}
