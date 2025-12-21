import Sidebar from "@/components/sidebar/Sidebar";
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    return (
        <div className="flex min-h-screen bg-zinc-50 font-sans dark:bg-black">
            <Sidebar>
                {children}
            </Sidebar>
        </div>
    )
}