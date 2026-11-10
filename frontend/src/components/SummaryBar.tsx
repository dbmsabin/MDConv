import type { ConvertResult } from "@/types";

interface SummaryBarProps {
  results: ConvertResult[];
}

export function SummaryBar({ results }: SummaryBarProps) {
  if (results.length === 0) return null;

  const ok = results.filter((r) => r.status === "ok");
  const errors = results.filter((r) => r.status === "error");
  const skipped = results.filter((r) => r.status === "skipped");
  const totalTokens = ok.reduce((sum, r) => sum + r.tokens_est, 0);

  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground px-1">
      <span>
        <span className="font-medium text-foreground">{ok.length}</span> converted
      </span>
      {errors.length > 0 && (
        <>
          <span>•</span>
          <span>
            <span className="font-medium text-destructive">{errors.length}</span> failed
          </span>
        </>
      )}
      {skipped.length > 0 && (
        <>
          <span>•</span>
          <span>
            <span className="font-medium">{skipped.length}</span> skipped
          </span>
        </>
      )}
      {ok.length > 0 && (
        <>
          <span>•</span>
          <span>~{totalTokens.toLocaleString()} tokens total</span>
        </>
      )}
    </div>
  );
}

