
import { Chart } from "@/components/chart/Chart";

export default function OverviewPage() {
    return (
        <div>
            {/* <div className="mb-8">
                <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">Overview</h1>
                <p className="mt-2 text-zinc-600 dark:text-zinc-400">
                    Welcome to your dashboard overview.
                </p>
            </div>

            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
                    <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">Running Tasks</p>
                    <p className="mt-2 text-3xl font-bold text-zinc-900 dark:text-white">{stats.runningTasks}</p>
                </div>
                <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
                    <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">Completed Tasks</p>
                    <p className="mt-2 text-3xl font-bold text-zinc-900 dark:text-white">{stats.completedTasks}</p>
                </div>
                <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
                    <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">Unseen Notifications</p>
                    <p className="mt-2 text-3xl font-bold text-zinc-900 dark:text-white">{stats.unseenNotifications}</p>
                </div>

            </div> */}
            <Chart />
        </div>
    );
}
