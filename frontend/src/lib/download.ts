import JSZip from "jszip";
import type { ConvertResult } from "@/types";

/** Download a text blob as a file. */
function saveAs(content: string, filename: string, mimeType = "text/markdown") {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

/** Download a single result's markdown. */
export function downloadSingle(result: ConvertResult) {
  const name = result.filename.replace(/\.[^.]+$/, "") + ".md";
  saveAs(result.markdown, name);
}

/**
 * Download all successful results as a zip archive.
 * Order is determined by the order of the `results` array (drag-to-reorder aware).
 */
export async function downloadAllAsZip(results: ConvertResult[]) {
  const zip = new JSZip();
  const ok = results.filter((r) => r.status === "ok");

  for (const result of ok) {
    const name = result.filename.replace(/\.[^.]+$/, "") + ".md";
    zip.file(name, result.markdown);
  }

  const blob = await zip.generateAsync({ type: "blob" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "converted.zip";
  a.click();
  URL.revokeObjectURL(url);
}

/**
 * Merge all successful results into a single .md file, separated by HR + heading.
 * Returns the full text so the caller can display the token estimate first.
 */
export function buildMerged(results: ConvertResult[]): string {
  const ok = results.filter((r) => r.status === "ok");
  return ok
    .map((r) => `# ${r.filename.replace(/\.[^.]+$/, "")}\n\n${r.markdown}`)
    .join("\n\n---\n\n");
}

export function downloadMerged(results: ConvertResult[]) {
  const merged = buildMerged(results);
  saveAs(merged, "merged.md");
}

/** Rough token estimate for a merged text. */
export function estimateTokens(text: string): number {
  return Math.round(text.length / 4);
}

