import { Button } from "@/components/ui/button";
import { Download, FileDown, Trash2 } from "lucide-react";
import { downloadAllAsZip, downloadMerged, buildMerged, estimateTokens } from "@/lib/download";
import { toast } from "sonner";
import type { ConvertResult } from "@/types";

interface ToolbarProps {
  results: ConvertResult[];
  onClear: () => void;
  disabled?: boolean;
}

export function Toolbar({ results, onClear, disabled }: ToolbarProps) {
  const hasOk = results.some((r) => r.status === "ok");

  async function handleDownloadZip() {
    try {
      await downloadAllAsZip(results);
      toast.success("Downloaded as zip");
    } catch {
      toast.error("Failed to create zip");
    }
  }

  function handleDownloadMerged() {
    const merged = buildMerged(results);
    const tokens = estimateTokens(merged);
    downloadMerged(results);
    toast.success(`Downloaded merged.md (~${tokens.toLocaleString()} tokens)`);
  }

  if (!hasOk && results.length === 0) return null;

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <Button
        variant="outline"
        size="sm"
        onClick={handleDownloadZip}
        disabled={disabled || !hasOk}
      >
        <Download className="h-4 w-4 mr-1.5" />
        Download all (.zip)
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={handleDownloadMerged}
        disabled={disabled || !hasOk}
      >
        <FileDown className="h-4 w-4 mr-1.5" />
        Download merged (.md)
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={onClear}
        disabled={disabled}
        className="text-muted-foreground hover:text-destructive"
      >
        <Trash2 className="h-4 w-4 mr-1.5" />
        Clear all
      </Button>
    </div>
  );
}

