import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface PipelineTaskDetailsProps {
    name: string;
    description: string;
    tags: string[];
    projects: string[];
}

export function PipelineTaskDetails({ name, description, tags, projects }: PipelineTaskDetailsProps) {
  return (
    <Card className="w-full text-sm">
      <CardHeader>
        <CardTitle className="mb-1">{name}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-4">
          <div className="font-semibold mb-1 text-xs">Tags</div>
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
        <div>
          <div className="font-semibold mb-1 text-xs">Projects</div>
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
