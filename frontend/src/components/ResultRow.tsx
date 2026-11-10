import { useState, useRef } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  GripVertical,
  Eye,
  EyeOff,
  Download,
  Trash2,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { downloadSingle } from "@/lib/download";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import type { ConvertResult, ConverterName } from "@/types";
import { ERROR_REASON } from "@/types";

const SOURCE_TYPE_COLORS: Record<string, string> = {
  pdf: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  docx: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  doc: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  pptx: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
  ppt: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
  xlsx: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  xls: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  html: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
  htm: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
  csv: "bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400",
  txt: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  md: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
};

const PREVIEW_LINES = 50;

interface ResultRowProps {
  result: ConvertResult;
  index: number;
  onRename: (id: string, name: string) => void;
  onRemove: (id: string) => void;
  onAltConverter: (id: string, converter: ConverterName) => void;
}

export function ResultRow({ result, index, onRename, onRemove, onAltConverter }: ResultRowProps) {
  const [isRenaming, setIsRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState(result.filename);
  const [showPreview, setShowPreview] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: result.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const isError = result.status === "error";
  const isSkipped = result.status === "skipped";
  const badgeColor = SOURCE_TYPE_COLORS[result.source_type] ?? "bg-gray-100 text-gray-700";

  function startRename() {
    setRenameValue(result.filename);
    setIsRenaming(true);
    setTimeout(() => inputRef.current?.focus(), 0);
  }

  function commitRename() {
    const trimmed = renameValue.trim();
    if (trimmed && trimmed !== result.filename) {
      onRename(result.id, trimmed);
    }
    setIsRenaming(false);
  }

  function handleDownload() {
    downloadSingle(result);
    toast.success(`Downloaded ${result.filename.replace(/\.[^.]+$/, "")}.md`);
  }

  const previewText = result.markdown
    .split("\n")
    .slice(0, PREVIEW_LINES)
    .join("\n");

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        "group flex flex-col gap-2 rounded-lg border bg-card p-3 transition-shadow",
        isDragging && "shadow-lg ring-2 ring-primary/20",
        (isError || isSkipped) && "opacity-60"
      )}
    >
      {/* Main row */}
      <div className="flex items-center gap-2">
        {/* Drag handle */}
        <button
          className="cursor-grab text-muted-foreground/40 hover:text-muted-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded"
          aria-label="Drag to reorder"
          {...attributes}
          {...listeners}
        >
          <GripVertical className="h-4 w-4" />
        </button>

        {/* Index */}
        <span className="w-5 text-xs text-muted-foreground text-right shrink-0">
          {index + 1}
        </span>

        {/* Filename / rename input */}
        <div className="flex-1 min-w-0">
          {isRenaming ? (
            <Input
              ref={inputRef}
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              onBlur={commitRename}
              onKeyDown={(e) => {
                if (e.key === "Enter") commitRename();
                if (e.key === "Escape") setIsRenaming(false);
              }}
              className="h-7 text-sm"
            />
          ) : (
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={startRename}
                  className="truncate text-sm font-medium text-left hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded w-full"
                  title="Click to rename"
                >
                  {result.filename}
                </button>
              </TooltipTrigger>
              <TooltipContent>Click to rename</TooltipContent>
            </Tooltip>
          )}
        </div>

        {/* Source type badge */}
        <span
          className={cn(
            "shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold uppercase tracking-wide",
            badgeColor
          )}
        >
          {result.source_type}
        </span>

        {/* Stats */}
        {result.status === "ok" && (
          <span className="hidden sm:block text-xs text-muted-foreground shrink-0 whitespace-nowrap">
            {result.words.toLocaleString()} words • {result.tokens_est.toLocaleString()} tokens
          </span>
        )}

        {/* Low text warning */}
        {result.low_text && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Badge variant="outline" className="shrink-0 border-amber-400 text-amber-600 dark:text-amber-400 gap-1">
                <AlertTriangle className="h-3 w-3" />
                Low text
              </Badge>
            </TooltipTrigger>
            <TooltipContent>May be scanned — text may be incomplete</TooltipContent>
          </Tooltip>
        )}

        {/* Error badge */}
        {isError && result.error_code && (
          <Badge variant="destructive" className="shrink-0 text-xs">
            {ERROR_REASON[result.error_code] ?? result.error}
          </Badge>
        )}

        {/* Action buttons */}
        <div className="flex items-center gap-1 shrink-0">
          {/* Preview toggle */}
          {result.status === "ok" && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  size="icon"
                  variant="ghost"
                  className="h-7 w-7"
                  onClick={() => setShowPreview((p) => !p)}
                  aria-label={showPreview ? "Hide preview" : "Show preview"}
                >
                  {showPreview ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                </Button>
              </TooltipTrigger>
              <TooltipContent>{showPreview ? "Hide preview" : "Preview"}</TooltipContent>
            </Tooltip>
          )}

          {/* Try alternate converter */}
          {isError && result.retryable && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 text-xs"
                  onClick={() =>
                    onAltConverter(
                      result.id,
                      result.converter === "markitdown" ? "pymupdf4llm" : "markitdown"
                    )
                  }
                >
                  <RefreshCw className="h-3 w-3 mr-1" />
                  Try alternate
                </Button>
              </TooltipTrigger>
              <TooltipContent>Re-convert using the alternate converter</TooltipContent>
            </Tooltip>
          )}

          {/* Not retryable hint */}
          {isError && !result.retryable && (
            <span className="text-xs text-muted-foreground hidden sm:block">
              Re-download the file and drop it in again
            </span>
          )}

          {/* Download */}
          {result.status === "ok" && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  size="icon"
                  variant="ghost"
                  className="h-7 w-7"
                  onClick={handleDownload}
                  aria-label="Download"
                >
                  <Download className="h-3.5 w-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Download .md</TooltipContent>
            </Tooltip>
          )}

          {/* Remove */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                size="icon"
                variant="ghost"
                className="h-7 w-7 text-muted-foreground hover:text-destructive"
                onClick={() => onRemove(result.id)}
                aria-label="Remove"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Remove</TooltipContent>
          </Tooltip>
        </div>
      </div>

      {/* Preview pane */}
      {showPreview && result.status === "ok" && (
        <pre className="rounded-md bg-muted p-3 text-xs overflow-auto max-h-72 font-mono whitespace-pre-wrap">
          {previewText}
          {result.markdown.split("\n").length > PREVIEW_LINES && (
            <span className="text-muted-foreground">
              {"\n"}… ({result.markdown.split("\n").length - PREVIEW_LINES} more lines)
            </span>
          )}
        </pre>
      )}
    </div>
  );
}

