# CLAUDE.md — Project rules for the AI

## Project
Personal "anything to Markdown" converter. Drop files or a zip (docx, pdf, pptx, xlsx, html, csv, txt) -> get `.md` files. Purpose: feed assignments to AI using fewer tokens.

**Layout:** `backend/` (FastAPI) and `frontend/` (React + Vite). Keep them independent; they talk only through the API in `api_spec.md`.

**Before any task, read:** `prd.md`, `implementation_plan.md`. For API/data work also read `api_spec.md` and `data_model.md`. For UI work read `ui_notes.md`.

## Stack
- Backend: Python 3.12, FastAPI, uvicorn, MarkItDown (+ pymupdf4llm as PDF fallback)
- Frontend: React 18 + TypeScript + Vite, Tailwind CSS, shadcn/ui (Radix + Lucide icons), react-dropzone, dnd-kit (reorder), JSZip, sonner (toasts)
- Packaging: Docker multi-stage build (Node builds frontend, Python image serves it), docker-compose
- Cloud (later): S3, CloudFront, ECR, Lambda container image, CloudWatch

## Rules
1. Work on ONE task from `implementation_plan.md` at a time. Do not build ahead.
2. Do not add features listed under "Out of scope" in `prd.md`.
3. Reuse libraries (MarkItDown etc.) before writing custom parsing.
4. Keep files small: backend logic in `backend/app/`, one responsibility per module. Frontend: one component per file in `frontend/src/components/`.
5. Never store uploaded files permanently. Use temp dirs and delete after the request.
6. Ignore `__MACOSX/`, `.DS_Store`, `Thumbs.db` and hidden files inside zips.
7. Protect against zip-slip (no `..` or absolute paths) and zip bombs (size/file-count limits).
8. If a file fails to convert, return an error for that file and continue with the rest.
9. No new dependency without saying why.
10. After finishing a task, tick it in `implementation_plan.md` and update `setup.md` if commands changed.

## Commands
- Backend dev: `cd backend && uvicorn app.main:app --reload` (port 8000)
- Frontend dev: `cd frontend && npm run dev` (port 5173, proxies `/api` to 8000)
- Backend tests: `cd backend && pytest`
- Frontend checks: `cd frontend && npm run lint && npm run build`
- Docker: `docker compose up --build`

## Style
- Python: type hints, small functions, docstrings only where non-obvious.
- TypeScript: strict mode, no `any`. Types mirror `data_model.md` in `frontend/src/types.ts`.
- React: function components + hooks only. Keep state in one `useConverter` hook; components stay presentational.
- UI: use shadcn/ui components first (`npx shadcn@latest add <name>`); do not hand-write what shadcn already provides. Tailwind utility classes only, no custom CSS files except `index.css`.
- Do not add UI libraries beyond those listed in the Stack section without saying why.
- Explain changes briefly; this is also a learning project (Docker + AWS).
