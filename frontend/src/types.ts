// Data model — mirrors the backend ConvertResult and API response shapes.

export type ConvertStatus = "ok" | "error" | "skipped";

export type ErrorCode =
  | "unsupported"
  | "parse_error"
  | "empty"
  | "timeout"
  | "memory"
  | "unknown"
  | null;

export type ConverterName = "markitdown" | "pymupdf4llm" | "none" | "auto";

export interface ConvertResult {
  id: string;
  filename: string;
  /** Relative path as it appeared inside a zip, or just the filename */
  path: string;
  source_type: string;
  status: ConvertStatus;
  markdown: string;
  words: number;
  tokens_est: number;
  low_text: boolean;
  error: string | null;
  error_code: ErrorCode;
  converter: ConverterName;
  retryable: boolean;
}

export interface ConvertSummary {
  total: number;
  ok: number;
  error: number;
  skipped: number;
}

export interface ConvertResponse {
  results: ConvertResult[];
  summary: ConvertSummary;
}

/** Map error codes to human-readable reasons (used by frontend display). */
export const ERROR_REASON: Record<NonNullable<ErrorCode>, string> = {
  unsupported: "File type not supported",
  parse_error: "Could not read file — it may be corrupt or encrypted",
  empty: "File appears to be empty",
  timeout: "Conversion timed out",
  memory: "Not enough memory to convert this file",
  unknown: "Unexpected error during conversion",
};

