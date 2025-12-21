import { cn } from "@/lib/utils";
import { FileItem } from "./FileItem";

interface FileListProps {
  uploadedFiles: File[];
  fileProgresses: Record<string, number>;
  removeFile: (filename: string) => void;
}

export function UploadedFileList({
  uploadedFiles,
  fileProgresses,
  removeFile,
}: FileListProps) {
  if (uploadedFiles.length === 0) {
    return null;
  }

  return (
    <div className={cn("px-6 pb-5 space-y-3 mt-4")}>
      {uploadedFiles.map((file, index) => (
        <FileItem
          key={file.name + index}
          file={file}
          progress={fileProgresses[file.name] || 0}
          onRemove={removeFile}
        />
      ))}
    </div>
  );
}
