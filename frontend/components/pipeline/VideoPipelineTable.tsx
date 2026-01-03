"use client";

import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { VideoPipelineStage, VideoPipelineStatus, SourceType } from "@/lib/sdk/types";
import { useRouter } from "next/navigation";

export interface VideoPipelineTableItem {
  id: string;
  path_id: string;
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

function getCurrentStage(stage: VideoPipelineStage) {
  switch (stage) {
    case VideoPipelineStage.INITIALIZED:
      return (
        <Badge
          variant="outline"
          className="bg-amber-500/15 text-amber-700 hover:bg-amber-500/25 dark:bg-amber-500/10 dark:text-amber-300 dark:hover:bg-amber-500/20 border-0"
        >
          Initialized
        </Badge>
      );
    case VideoPipelineStage.DOCUMENT_PROCESSING:
      return (
        <Badge
          variant="outline"
          className="bg-blue-500/15 text-blue-700 hover:bg-blue-500/25 dark:bg-blue-500/10 dark:text-blue-400 dark:hover:bg-blue-500/20 border-0"
        >
          Document Processing
        </Badge>
      );
    case VideoPipelineStage.IMAGE_PROCESSING:
      return (
        <Badge
          variant="outline"
          className="bg-blue-500/15 text-blue-700 hover:bg-blue-500/25 dark:bg-blue-500/10 dark:text-blue-400 dark:hover:bg-blue-500/20 border-0"
        >
          Image Processing
        </Badge>
      );
    case VideoPipelineStage.CONTENT_ANALYSIS:
      return (
        <Badge
          variant="outline"
          className="bg-blue-500/15 text-blue-700 hover:bg-blue-500/25 dark:bg-blue-500/10 dark:text-blue-400 dark:hover:bg-blue-500/20 border-0"
        >
          Content Analysis
        </Badge>
      );
    case VideoPipelineStage.SCRIPT_GENERATION:
      return (
        <Badge
          variant="outline"
          className="bg-blue-500/15 text-blue-700 hover:bg-blue-500/25 dark:bg-blue-500/10 dark:text-blue-400 dark:hover:bg-blue-500/20 border-0"
        >
          Script Generation
        </Badge>
      );
    case VideoPipelineStage.VIDEO_GENERATION:
      return (
        <Badge
          variant="outline"
          className="bg-blue-500/15 text-blue-700 hover:bg-blue-500/25 dark:bg-blue-500/10 dark:text-blue-400 dark:hover:bg-blue-500/20 border-0"
        >
          Video Generation
        </Badge>
      );
    default:
      return <Badge variant="secondary">{stage}</Badge>;
  }
}

function getStatusBadge(status: VideoPipelineTableItem["status"]) {
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

interface VideoPipelineTableProps {
  videoPipelines: VideoPipelineTableItem[];
}

export default function VideoPipelineTable({ videoPipelines = [] }: VideoPipelineTableProps) {
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
          {getCurrentStage(videoPipeline.current_stage)}
        </TableCell>
        <TableCell className="h-16 px-2 w-[90px]">
          {getStatusBadge(videoPipeline.status)}
        </TableCell>
        <TableCell className="h-16 px-2 text-sm text-muted-foreground w-[90px]">
          {videoPipeline.source_type.toUpperCase()}
        </TableCell>
        <TableCell className="h-16 px-2 text-sm text-muted-foreground w-[90px]">
          {dateTimeFormat.format(new Date(videoPipeline.created_at))}
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
            <TableHead className="h-12 px-2 font-medium w-[15%]">Description</TableHead>
            <TableHead className="h-12 px-2 font-medium w-[15%]">Current Stage</TableHead>
            <TableHead className="h-12 px-2 font-medium w-[10%]">Status</TableHead>
            <TableHead className="h-12 px-2 font-medium w-[10%]">Source Type</TableHead>
            <TableHead className="h-12 px-2 font-medium w-[10%]">Created At</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>{videoPipelines.map(renderVideoPipelineRow)}</TableBody>
      </Table>
    </div>
  );
}