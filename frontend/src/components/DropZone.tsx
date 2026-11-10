import { useDropzone } from "react-dropzone";
import { Upload } from "lucide-react";
import { cn } from "@/lib/utils";

interface DropZoneProps {
  onDrop: (files: File[]) => void;
  disabled?: boolean;
}

export function DropZone({ onDrop, disabled }: DropZoneProps) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    disabled,
    multiple: true,
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-14 transition-colors cursor-pointer",
        isDragActive
          ? "border-primary bg-primary/5"
          : "border-muted-foreground/30 hover:border-primary/50 hover:bg-muted/30",
        disabled && "pointer-events-none opacity-50"
      )}
    >
      <input {...getInputProps()} />
      <Upload
        className={cn(
          "h-10 w-10 transition-colors",
          isDragActive ? "text-primary" : "text-muted-foreground"
        )}
      />
      <div className="text-center">
        <p className="text-sm font-medium">
          {isDragActive ? "Drop files here" : "Drop files or a zip here, or click to select"}
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          Supports DOCX, PDF, PPTX, XLSX, HTML, CSV, TXT and ZIP archives
        </p>
      </div>
    </div>
  );
}

