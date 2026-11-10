import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";
import { FileText, Loader2 } from "lucide-react";
import { DropZone } from "@/components/DropZone";
import { SummaryBar } from "@/components/SummaryBar";
import { Toolbar } from "@/components/Toolbar";
import { ResultList } from "@/components/ResultList";
import { ErrorBanner } from "@/components/ErrorBanner";
import { useConverter } from "@/hooks/useConverter";

export default function App() {
  const {
    results,
    loading,
    globalError,
    handleDrop,
    retryAll,
    tryAltConverter,
    reorder,
    rename,
    remove,
    clearAll,
  } = useConverter();

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-background">
        <div className="mx-auto max-w-[900px] px-4 py-10 flex flex-col gap-6">
          {/* Header */}
          <header className="text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <FileText className="h-7 w-7 text-primary" />
              <h1 className="text-2xl font-bold tracking-tight">MDConv</h1>
            </div>
            <p className="text-sm text-muted-foreground">
              Drop files or a zip → get clean Markdown. Optimized for AI context.
            </p>
          </header>

          {/* Drop zone */}
          <DropZone onDrop={handleDrop} disabled={loading} />

          {/* Loading spinner */}
          {loading && (
            <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Converting files…
            </div>
          )}

          {/* Global error banner */}
          {globalError && (
            <ErrorBanner message={globalError} onRetry={retryAll} />
          )}

          {/* Summary + Toolbar */}
          {results.length > 0 && !loading && (
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <SummaryBar results={results} />
              <Toolbar
                results={results}
                onClear={clearAll}
                disabled={loading}
              />
            </div>
          )}

          {/* Result list */}
          <ResultList
            results={results}
            onReorder={reorder}
            onRename={rename}
            onRemove={remove}
            onAltConverter={tryAltConverter}
          />
        </div>
      </div>
      <Toaster />
    </TooltipProvider>
  );
}
