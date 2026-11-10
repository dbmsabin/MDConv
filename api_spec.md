# API Spec

Base URL (dev): `http://localhost:8000`, called from the Vite dev server through its `/api` proxy.
In Docker the built frontend and API share one origin.

All routes below are mounted under the `/api` prefix (e.g. `POST /api/convert`).

## GET /health
Response `200`:
```json
{ "status": "ok" }
```

## POST /convert
Content-Type: `multipart/form-data`

| Field | Type | Notes |
|---|---|---|
| `files` | file (repeatable) | Any supported file or a `.zip` |

Behavior:
1. Save uploads to a temp dir.
2. Extract zips safely (see `CLAUDE.md` rules 6-7). Nested zips: one level only.
3. Convert each supported file. One failure must not stop the others.
4. Delete the temp dir before responding.

Response `200`:
```json
{
  "results": [
    {
      "id": "b1c2...",
      "filename": "Assignment1.docx",
      "path": "week2/Assignment1.docx",
      "source_type": "docx",
      "status": "ok",
      "markdown": "# Assignment 1\n...",
      "words": 842,
      "tokens_est": 1190,
      "low_text": false,
      "error": null,
      "error_code": null,
      "converter": "markitdown",
      "retryable": false
    }
  ],
  "summary": { "total": 12, "ok": 10, "error": 1, "skipped": 1 }
}
```

Errors:
| Code | When |
|---|---|
| `400` | No files provided |
| `413` | Upload larger than `MAX_UPLOAD_MB` |
| `422` | Malformed form data |
| `500` | Unexpected server error (body: `{ "detail": "..." }`) |

A bad file inside a valid request is NOT an HTTP error. It appears in `results` with `status: "error"`.

## POST /convert-alt
Re-converts ONE file using the alternate converter. Used by the "Try alternate converter" button.

Content-Type: `multipart/form-data`

| Field | Type | Notes |
|---|---|---|
| `file` | file | The original file again (the server keeps nothing between requests) |
| `converter` | string | `pymupdf4llm` (PDF only for now) or `markitdown` |

Response `200`: a single `ConvertResult` object (same shape as items in `results`).
Errors: `400` missing file, `415` converter does not support this file type.

Failed items in `/convert` responses look like:
```json
{
  "filename": "scan.pdf",
  "status": "error",
  "markdown": "",
  "error": "Could not read file",
  "error_code": "parse_error",
  "converter": "markitdown",
  "retryable": true
}
```

Frontend note: keep the original `File` object in memory so it can be re-sent for `/convert-alt` without asking the user to re-upload.

## CORS
Allow the frontend origin only (configurable via `ALLOWED_ORIGINS`). Needed for dev (`http://localhost:5173`) and for the CloudFront origin on AWS. Not needed when the Vite proxy or Docker same-origin setup is used.

## Later (AWS phase)
- `POST /presign` -> `{ "upload_url": "...", "key": "..." }` for direct S3 upload.
- `POST /convert-s3` with `{ "keys": [...] }` -> same response shape as `/convert`.
