import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card"
import { VideoPipelineStage, VideoPipelineStatus } from "@/lib/sdk/types"
import { VideoPipelineStageBadge } from "./video-pipeline-stage-badge"
import { VideoPipelineStatusBadge } from "./video-pipeline-status-badge"
import { formatDate } from "@/lib/utils"

interface PipelineTaskDetailsProps {
    name: string;
    instructions: string;
    created_at?: string;
    current_stage?: VideoPipelineStage;
    status?: VideoPipelineStatus;
}

export function VideoPipelineDetails({ 
  name, 
  instructions, 
  created_at,
  current_stage,
  status
}: PipelineTaskDetailsProps) {
  return (
    <Card className="w-full text-sm">
      <CardHeader>
        <CardTitle className="mb-1">{name}</CardTitle>
        <CardDescription className="italic">{instructions}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Status and Stage Row */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-4">
            {status && (
              <div className="flex items-center gap-2">
                <VideoPipelineStatusBadge status={status} />
              </div>
            )}
            {current_stage && (
              <div className="flex items-center gap-2">
                <VideoPipelineStageBadge stage={current_stage} />
              </div>
            )}
          </div>
          {created_at && (
            <div className="flex items-center gap-2">
              <span className="text-xs">{formatDate(created_at)}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

