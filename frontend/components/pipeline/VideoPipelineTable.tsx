"use client";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { SourceType, VideoPipelineStage, VideoPipelineStatus } from "@/lib/sdk/types";
import { useRouter } from "next/navigation";
import { VideoPipelineStageBadge } from "./VideoPipelineStageBadge";
import { VideoPipelineStatusBadge } from "./VideoPipelineStatusBadge";
import { VideoPipelineDeleteButton } from "./VideoPipelineDeleteButton";

export interface VideoPipelineTableItem {
  id: string;
  name: string;
  description: string;
  tags: string[];
  projects: string[];
  updated_at: string;
  created_at: string;
  source_path: string;
  source_type: SourceType;
  current_stage: VideoPipelineStage;
  status: VideoPipelineStatus;
}


interface VideoPipelineTableProps {
  videoPipelines: VideoPipelineTableItem[];
  onDelete: (videoPipeline: VideoPipelineTableItem) => void;
}

export default function VideoPipelineTable({ videoPipelines = [], onDelete }: VideoPipelineTableProps) {
  const router = useRouter();

  const handleVideoPipelineClick = (videoPipeline: VideoPipelineTableItem) => {
    router.push(`/video-pipelines/${videoPipeline.id}`);
  };

  const renderVideoPipelineRow = (videoPipeline: VideoPipelineTableItem) => {
    const dateTimeFormat = new Intl.DateTimeFormat('en', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });

    return (
      <TableRow key={videoPipeline.id} className="hover:bg-muted/50" onClick={() => handleVideoPipelineClick(videoPipeline)}>
        <TableCell className="px-2 h-16 px-2 font-medium">{videoPipeline.name}</TableCell>
        <TableCell className="h-16 px-2 text-sm text-muted-foreground">
          {videoPipeline.description.length > 100 ? videoPipeline.description.substring(0, 100) + "..." : videoPipeline.description}
        </TableCell>
        <TableCell className="h-16 px-2 text-sm text-muted-foreground w-[90px]">
          <VideoPipelineStageBadge stage={videoPipeline.current_stage} />
        </TableCell>
        <TableCell className="h-16 px-2 w-[90px]">
          <VideoPipelineStatusBadge status={videoPipeline.status} />
        </TableCell>
        <TableCell className="h-16 px-2 text-sm text-muted-foreground w-[90px]">
          {videoPipeline.source_type.toUpperCase()}
        </TableCell>
        <TableCell className="h-16 px-2 text-sm text-muted-foreground w-[90px]">
          {dateTimeFormat.format(new Date(videoPipeline.created_at))}
        </TableCell>
        <TableCell className="h-16 px-2 text-sm text-muted-foreground w-[90px]">
          <VideoPipelineDeleteButton videoPipeline={videoPipeline} onDelete={onDelete} />
        </TableCell>
      </TableRow>
    );
  };

  return (
    <div className="rounded-lg border bg-card w-full overflow-x-auto">
      <Table className="min-w-[370px] w-full">
        <TableHeader>
          <TableRow className="hover:bg-transparent border-b">
            <TableHead className="px-2 h-12 px-2 font-medium w-[10%]">Title</TableHead>
            <TableHead className="h-12 px-2 font-medium w-[10%]">Description</TableHead>
            <TableHead className="h-12 px-2 font-medium w-[10%]">Current Stage</TableHead>
            <TableHead className="h-12 px-2 font-medium w-[10%]">Status</TableHead>
            <TableHead className="h-12 px-2 font-medium w-[10%]">Source Type</TableHead>
            <TableHead className="h-12 px-2 font-medium w-[10%]">Created At</TableHead>
            <TableHead className="h-12 px-2 font-medium w-[10%]">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>{videoPipelines.map(renderVideoPipelineRow)}</TableBody>
      </Table>
    </div>
  );
}