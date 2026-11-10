# UI Notes

Single page React app using shadcn/ui + Tailwind. Clean and fast, desktop first.

## Layout (top to bottom)
1. **Header:** app name + short tagline.
2. **Drop zone:** large dashed box. Text: "Drop files or a zip here, or click to select". Accepts multiple files. Highlights on drag-over.
3. **Status bar:** appears after conversion, e.g. "10 converted, 1 failed, 1 skipped • ~12,400 tokens total".
4. **Toolbar:** `Download all (.zip)` • `Download merged (.md)` • `Clear all`.
5. **Result list:** one row per file.

## Row contents
- Drag handle (left) for reordering
- Order number
- Output filename (click to rename inline)
- Source type badge (DOCX, PDF...)
- Words • est. tokens
- Warning badge "Low text, may be scanned" if `low_text`
- Error badge with the readable reason (from `error_code`); row is greyed and excluded from downloads
- If `retryable` is true: a "Try alternate converter" button on that row. No generic retry icon, since deterministic failures would fail again.
- If not retryable: hint text such as "Re-download the file and drop it in again", plus Remove
- Buttons: Preview (expand), Download, Remove

## Behavior
- Drag to reorder rows; order drives zip order and merged file order.
- Preview expands a `<pre>` with the first ~50 lines.
- If the whole `/convert` request fails (network error or 5xx), show a banner with a "Retry all" button. Keep the selected files in memory so nothing needs re-selecting.
- Loading state: spinner while `/convert` runs; disable toolbar.
- Merged download shows the combined token estimate before downloading.
- Everything lives in memory; refresh clears the list (acceptable for MVP).

## Component mapping
| UI piece | Implementation |
|---|---|
| Drop zone | `react-dropzone` inside a shadcn-styled `Card`; accepts multiple files and zips |
| Buttons | shadcn `Button` (variants: default, outline, ghost, destructive) |
| Type badge, warning/error badges | shadcn `Badge` |
| Row container | shadcn `Card` or a bordered `div` with Tailwind |
| Reorder | `dnd-kit` (`SortableContext` + `useSortable`), drag handle uses Lucide `GripVertical` |
| Inline rename | shadcn `Input`, shown on click |
| Loading | shadcn `Progress` or a Lucide `Loader2` spinner |
| Toasts (copied, downloaded, failed) | `sonner` |
| Hints/tooltips | shadcn `Tooltip` |
| Row actions menu (optional) | shadcn `DropdownMenu` |
| Icons | `lucide-react` (`FileText`, `Download`, `Trash2`, `RefreshCw`, `AlertTriangle`) |

## Components (frontend/src/components)
`DropZone`, `SummaryBar`, `Toolbar`, `ResultList`, `ResultRow`, `ErrorBanner`. State lives in `hooks/useConverter.ts`; components receive props only.

## Style
- shadcn default theme (neutral), max-width 900px, centered, Tailwind spacing scale.
- Dark mode via shadcn's `dark` class, following `prefers-color-scheme` by default.
- Colors: neutral grey, one accent color; green/amber/red only for ok/warning/error.
- Keyboard accessible: buttons focusable, visible focus ring.

## Not needed
- No Markdown rendering, no editor, no login, no settings page.
