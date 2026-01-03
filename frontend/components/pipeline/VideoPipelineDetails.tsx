import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { VideoPipelineStage, VideoPipelineStatus } from "@/lib/sdk/types"
import { VideoPipelineStageBadge } from "./VideoPipelineStageBadge"
import { VideoPipelineStatusBadge } from "./VideoPipelineStatusBadge"
import { formatDate } from "@/lib/utils"

interface PipelineTaskDetailsProps {
    name: string;
    description: string;
    tags: string[];
    projects: string[];
    created_at?: string;
    current_stage?: VideoPipelineStage;
    status?: VideoPipelineStatus;
}

export function VideoPipelineDetails({ 
  name, 
  description, 
  tags, 
  projects,
  created_at,
  current_stage,
  status
}: PipelineTaskDetailsProps) {
  return (
    <Card className="w-full text-sm">
      <CardHeader>
        <CardTitle className="mb-1">{name}</CardTitle>
        <CardDescription className="italic">{description}</CardDescription>
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

        {/* tags section */}
        <div>
          <div className="font-semibold mb-2 text-xs">Tags</div>
          <div className="flex flex-wrap gap-2">
            {tags.length > 0 ? (
              tags.map((tag, idx) => (
                <Badge key={idx} variant="secondary">{tag}</Badge>
              ))
            ) : (
              <span className="text-muted-foreground text-xs">No tags</span>
            )}
          </div>
        </div>

        {/* projects section */}
        <div>
          <div className="font-semibold mb-2 text-xs">Projects</div>
          <div className="flex flex-wrap gap-2">
            {projects.length > 0 ? (
              projects.map((project, idx) => (
                <Badge key={idx} variant="outline">{project}</Badge>
              ))
            ) : (
              <span className="text-muted-foreground text-xs">No projects</span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
