# Implementation Plan

Tick tasks as done. One task at a time.

## Phase 1 — Local app
- [x] 1.1 Backend skeleton: `backend/app/main.py`, `converter.py`, `zip_utils.py`, `backend/requirements.txt`; mount routes under `/api`
- [x] 1.2 `GET /health` endpoint
- [x] 1.3 `converter.py`: convert one file path -> markdown using MarkItDown, return result object
- [x] 1.4 PDF fallback with pymupdf4llm when MarkItDown output is near-empty
- [x] 1.5 `zip_utils.py`: safe extraction (skip junk, block zip-slip, limit size and file count)
- [x] 1.6 `POST /convert`: accept multiple files and zips, return list of results (see `api_spec.md`)
- [x] 1.6a Classify failures into `error_code` values (see `data_model.md`) and set `retryable`
- [x] 1.6b Backend auto-retry once for `timeout` and `memory` only; never retry deterministic errors
- [x] 1.6c `POST /convert-alt` endpoint: re-convert one file with the alternate converter (see `api_spec.md`)
- [x] 1.7 Word count + estimated token count (chars / 4)
- [x] 1.8 Low-text warning flag
- [x] 1.9a Frontend scaffold: Vite + React + TS, Tailwind, shadcn init, Vite proxy to `/api`
- [x] 1.9b `types.ts` (mirror `data_model.md`) and `lib/api.ts` (`convertFiles`, `convertAlt`)
- [x] 1.9c `DropZone` with react-dropzone, calls `/api/convert`, loading state via `useConverter` hook
- [x] 1.10 `ResultList` + `ResultRow`: badges, preview, remove, inline rename, `SummaryBar` totals
- [x] 1.10a Frontend: show the readable error reason on failed rows (from `error_code`)
- [x] 1.10b Frontend: "Try alternate converter" button, shown only when `retryable` is true; replaces the row's result on success
- [x] 1.10c Frontend: "Retry all" banner when the whole `/convert` request fails (network error or 5xx)
- [x] 1.11 Drag-to-reorder with dnd-kit (drag handle, keyboard support)
- [x] 1.12 `lib/download.ts`: download single, download all (JSZip), download merged `.md`; wire to `Toolbar`; sonner toasts
- [x] 1.13 Basic tests with sample files (docx, pdf, pptx, zip, corrupt file)

## Phase 2 — Docker
- [x] 2.1 Multi-stage `Dockerfile`: stage 1 `node:20-alpine` builds the frontend, stage 2 `python:3.12-slim` runs uvicorn as non-root and serves `dist/`
- [x] 2.2 `.dockerignore`
- [x] 2.3 `docker-compose.yml` (single service; optional dev profile with Vite hot reload and volume mounts)
- [ ] 2.4 Verify build, run, and port mapping; compare image size with and without multi-stage; check build-cache behavior after changing one file

## Phase 3 — AWS
- [ ] 3.0 Create Budgets alarm ($1) and a non-root IAM user first
- [ ] 3.1 `npm run build`, upload `frontend/dist` to S3, serve via CloudFront (set `VITE_API_URL`)
- [ ] 3.2 Push image to ECR
- [ ] 3.3 Lambda (container image) + Function URL
- [ ] 3.4 S3 presigned upload flow for large zips
- [ ] 3.5 S3 lifecycle rule: delete uploads after 1 day
- [ ] 3.6 CloudWatch logs check, least-privilege IAM role

## Phase 4 — Polish
- [ ] 4.1 IaC with AWS SAM or CDK
- [ ] 4.2 GitHub Actions: build + deploy
- [ ] 4.3 Optional: OCR for scanned PDFs (Tesseract)
