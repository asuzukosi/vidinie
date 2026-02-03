import { Badge } from "@/components/ui/badge";
import { VideoPipelineStatus } from "@/lib/sdk/types";

interface VideoPipelineStatusBadgeProps {
  status: VideoPipelineStatus;
}

export function VideoPipelineStatusBadge({ status }: VideoPipelineStatusBadgeProps) {
  switch (status) {
    case VideoPipelineStatus.PENDING:
      return (
        <Badge
          variant="outline"
          className="bg-amber-500/15 text-amber-700 hover:bg-amber-500/25 dark:bg-amber-500/10 dark:text-amber-300 dark:hover:bg-amber-500/20 border-0"
        >
          Pending
        </Badge>
      );
    case VideoPipelineStatus.IN_PROGRESS:
      return (
        <Badge
          variant="outline"
          className="bg-blue-500/15 text-blue-700 hover:bg-blue-500/25 dark:bg-blue-500/10 dark:text-blue-400 dark:hover:bg-blue-500/20 border-0"
        >
          In Progress
        </Badge>
      );
    case VideoPipelineStatus.COMPLETED:
      return (
        <Badge
          variant="outline"
          className="bg-green-500/15 text-green-700 hover:bg-green-500/25 dark:bg-green-500/10 dark:text-green-400 dark:hover:bg-green-500/20 border-0"
        >
          Completed
        </Badge>
      );
    case VideoPipelineStatus.FAILED:
      return (
        <Badge
          variant="outline"
          className="bg-rose-500/15 text-rose-700 hover:bg-rose-500/25 dark:bg-rose-500/10 dark:text-rose-400 dark:hover:bg-rose-500/20 border-0"
        >
          Failed
        </Badge>
      );
    default:
      return <Badge variant="secondary">{status}</Badge>;
  }
}

