import type { ConvertResponse, ConvertResult, ConverterName } from "@/types";

const BASE = import.meta.env.VITE_API_URL ?? "";

/**
 * Convert one or more files (including .zip) by POSTing to /api/convert.
 * Throws on network errors or HTTP 5xx/4xx.
 */
export async function convertFiles(files: File[]): Promise<ConvertResponse> {
  const form = new FormData();
  for (const file of files) {
    form.append("files", file);
  }

  const res = await fetch(`${BASE}/api/convert`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Server error ${res.status}: ${detail}`);
  }

  return res.json() as Promise<ConvertResponse>;
}

/**
 * Re-convert a single file using the alternate converter.
 * Returns one ConvertResult.
 */
export async function convertAlt(
  file: File,
  converter: ConverterName
): Promise<ConvertResult> {
  const form = new FormData();
  form.append("file", file);
  form.append("converter", converter);

  const res = await fetch(`${BASE}/api/convert-alt`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Server error ${res.status}: ${detail}`);
  }

  return res.json() as Promise<ConvertResult>;
}

