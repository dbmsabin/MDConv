# Setup

## Project structure
```
md2ai/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, routes, serves built frontend in production
│   │   ├── converter.py     # MarkItDown wrapper + PDF fallback
│   │   └── zip_utils.py     # safe zip extraction
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # DropZone, ResultList, ResultRow, Toolbar, ...
│   │   ├── hooks/           # useConverter.ts
│   │   ├── lib/             # api.ts, download.ts, utils.ts (shadcn)
│   │   ├── types.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── components.json      # shadcn config
├── Dockerfile               # multi-stage: node build -> python runtime
├── docker-compose.yml
├── .dockerignore
└── docs: CLAUDE.md prd.md implementation_plan.md data_model.md api_spec.md ui_notes.md setup.md
```

## Frontend setup (one time)
Requires Node 20+.
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install tailwindcss @tailwindcss/vite
# follow the shadcn Vite guide at ui.shadcn.com/docs/installation/vite, then:
npx shadcn@latest init
npx shadcn@latest add button badge card input progress sonner tooltip dropdown-menu
npm install react-dropzone @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities jszip lucide-react
```
Check the shadcn docs for the current init steps; they change between versions.

`vite.config.ts` needs a dev proxy so the frontend can call the API without CORS issues:
```ts
server: { proxy: { "/api": "http://localhost:8000" } }
```
(Backend routes are mounted under `/api` in production too, e.g. `/api/convert`.)

## backend/requirements.txt (starting point)
```
fastapi
uvicorn[standard]
python-multipart
markitdown[all]
pymupdf4llm
pytest
httpx
```

## Run locally
Two terminals:
```bash
# Terminal 1: backend
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload    # http://localhost:8000

# Terminal 2: frontend
cd frontend
npm install
npm run dev                      # http://localhost:5173  (open this one)
```

## Run with Docker
```bash
docker compose up --build
# open http://localhost:8000  (FastAPI serves the built React app)
docker compose down
```

### Dockerfile outline (multi-stage)
1. **Stage `frontend-build`:** `node:20-alpine`, copy `frontend/`, `npm ci`, `npm run build` -> `dist/`.
2. **Stage `runtime`:** `python:3.12-slim`, install `backend/requirements.txt`, copy `backend/app`, copy `dist/` from stage 1 into `app/static`, run uvicorn as a non-root user.

The final image contains no Node, no `node_modules`, only Python plus static files. That is the main thing to learn from the multi-stage build.

## Environment variables
| Name | Default | Purpose |
|---|---|---|
| `MAX_UPLOAD_MB` | 50 | Reject larger uploads |
| `MAX_ZIP_FILES` | 200 | Zip bomb protection |
| `MAX_UNZIPPED_MB` | 200 | Zip bomb protection |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | CORS (dev only; in Docker the app is same-origin) |

## AWS checklist (Phase 3)
1. Create account, enable MFA on root, create an IAM user for daily work.
2. Create a Budgets alarm at $1 BEFORE building anything.
3. Pick one region and stay in it (e.g. `ap-south-1`).
4. Frontend: run `npm run build`, upload `frontend/dist/` to a private S3 bucket, serve via CloudFront with Origin Access Control. Set `VITE_API_URL` to the Lambda Function URL at build time.
5. Image: `aws ecr create-repository`, then `docker build`, `docker tag`, `docker push`.
6. Lambda: create from container image, 1024-2048 MB memory, 60 s timeout, add Function URL.
7. Uploads bucket: lifecycle rule to expire objects after 1 day; Lambda role limited to that bucket.
8. Check logs in CloudWatch.
9. Check the current Free Tier terms on the AWS site; delete resources when done.

## Troubleshooting
- Empty output for a PDF: likely scanned; needs OCR (out of scope for MVP).
- `413` error: raise `MAX_UPLOAD_MB` or use the S3 flow.
- Frontend calls fail with CORS errors in dev: check the Vite proxy and that the backend is running on 8000.
- shadcn component missing: run `npx shadcn@latest add <name>`.
- Blank page after Docker build: confirm `dist/` was copied into the runtime stage and FastAPI mounts it.
