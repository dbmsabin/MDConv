# MDConv 📄➡️📝

> **Personal "Anything to Markdown" Converter** — Convert your documents, slides, spreadsheets, and archives into clean, LLM-ready Markdown to save tokens and maintain formatting when feeding context to AI assistants.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4.0-38B2AC?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com)

---

## 🎯 Purpose & Why MDConv?

Feeding large PDFs, Word documents, PowerPoint presentations, and Excel sheets directly to LLMs (like Claude, ChatGPT, or Gemini) often consumes excessive tokens, leads to parsing errors, or loses structural hierarchy.

**MDConv** transforms diverse documents and archives into concise, structured Markdown. It reduces token overhead significantly while preserving headings, tables, code blocks, and lists, making it ideal for:
- Course assignments and lecture slides
- Technical specifications and research papers
- Financial reports, spreadsheets, and data exports
- Multi-file codebases and project folders bundled in `.zip` archives

---

## ✨ Features

- **Multi-Format Ingestion**: Convert `.pdf`, `.docx`, `.pptx`, `.xlsx`, `.html`, `.csv`, `.txt`, and `.md`.
- **Zip Archive Unpacking**: Drag-and-drop a `.zip` file containing dozens of files across subdirectories; MDConv unzips and converts each document while preserving relative file paths.
- **Security-First Zip Handling**:
  - **Zip-Slip Protection**: Sanitizes file paths to prevent directory traversal exploits.
  - **Zip-Bomb Mitigation**: Enforces uncompressed file size and file count thresholds.
  - **Junk Filtering**: Automatically skips `__MACOSX/`, `.DS_Store`, `Thumbs.db`, and hidden system files.
- **Dual Conversion Engine with PDF Fallback**:
  - Primary converter: Microsoft's [MarkItDown](https://github.com/microsoft/markitdown) for rich multi-format parsing.
  - Intelligent PDF Fallback: Automatically falls back to [PyMuPDF4LLM](https://github.com/pymupdf/pymupdf4llm) if MarkItDown extracts low or near-empty text.
  - Manual Alternate Retry: One-click "Try alternate converter" button for individual files.
- **Token & Word Metrics**:
  - Real-time word count calculation.
  - Estimated AI token counter (`characters / 4`) to help you gauge LLM context limits before sending.
  - Low-text warning badge for potentially scanned documents or image-only PDFs.
- **Interactive Web Interface**:
  - Clean, drag-and-drop file upload zone via `react-dropzone`.
  - Drag-and-drop reordering with `@dnd-kit` to organize files before downloading.
  - Real-time Markdown preview drawer.
  - Inline filename editing and one-click clipboard copy.
- **Flexible Batch Export**:
  - Download individual `.md` files.
  - Download all converted files bundled into a single `.zip` (generated client-side with `JSZip`).
  - **Merge All**: Combine all converted documents into one continuous, divider-separated `.md` file for instant pasting into an LLM chat.
- **Self-Contained Deployment**: Single multi-stage Docker container that builds the React frontend and serves both the API and the static web app via FastAPI.

---

## 🏗️ Architecture & Tech Stack

```
MDConv/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application & REST endpoints (/api/health, /api/convert, /api/convert-alt)
│   │   ├── converter.py     # MarkItDown conversion logic + PyMuPDF4LLM fallback & token estimation
│   │   └── zip_utils.py     # Safe zip extraction & security guards
│   ├── tests/               # Pytest automated test suite
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # DropZone, ResultList, ResultRow, Toolbar, SummaryBar, ErrorBanner
│   │   ├── components/ui/   # Shadcn UI primitives (button, badge, input, tooltip, sonner)
│   │   ├── hooks/           # useConverter.ts custom state hook
│   │   ├── lib/             # api.ts (HTTP client), download.ts (JSZip export), utils.ts
│   │   ├── types.ts         # TypeScript interfaces matching API spec
│   │   ├── App.tsx          # Main application page
│   │   └── main.tsx
│   ├── vite.config.ts       # Vite configuration with API dev proxy
│   └── package.json
├── Dockerfile               # Multi-stage build (Node 20 -> Python 3.12-slim)
├── docker-compose.yml       # Production and dev compose configurations
└── .dockerignore
```

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.12, FastAPI, Uvicorn, MarkItDown, PyMuPDF4LLM, Pytest, HTTPX |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, Lucide Icons, dnd-kit, JSZip, Sonner |
| **Packaging** | Docker, Docker Compose |

---

## 🚀 Getting Started

### Option 1: Docker (Recommended)

The easiest way to run MDConv is with Docker Compose. This builds the frontend into static assets and serves the complete application from a lightweight Python container.

```bash
# Clone the repository
git clone https://github.com/dbmsabin/MDConv.git
cd MDConv

# Build and start the container
docker compose up --build
```

Open your browser and navigate to:
```
http://localhost:8000
```

To stop the container:
```bash
docker compose down
```

---

### Option 2: Local Development

If you are developing or contributing, you can run the backend and frontend separately with hot-reloading.

#### Prerequisites
- **Python**: 3.12+
- **Node.js**: 20+ and npm

#### 1. Start Backend

```bash
cd backend

# Create and activate virtual environment
# On Windows:
python -m venv .venv
.venv\Scripts\activate

# On macOS/Linux:
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI development server with reload
uvicorn app.main:app --reload --port 8000
```
Backend API will be accessible at `http://localhost:8000` (docs available at `http://localhost:8000/docs`).

#### 2. Start Frontend

In a separate terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

Open `http://localhost:5173` in your browser. Requests to `/api/*` are automatically proxied to `http://localhost:8000`.

---

## 🧪 Running Tests

### Backend Unit & Integration Tests

The test suite covers safe zip extraction, zip-bomb/zip-slip defenses, API endpoints, and document conversion across PDF, PPTX, and DOCX.

```bash
cd backend
pytest -v
```

### Frontend Build & Lint Verification

```bash
cd frontend
npm run lint
npm run build
```

---

## ⚙️ Configuration & Environment Variables

You can configure upload limits and behavior through environment variables:

| Variable | Default | Description |
|---|---|---|
| `MAX_UPLOAD_MB` | `50` | Maximum combined size of uploaded files per request in megabytes. |
| `MAX_ZIP_FILES` | `200` | Maximum number of files permitted to be extracted from a `.zip` archive. |
| `MAX_UNZIPPED_MB` | `200` | Maximum uncompressed payload limit in megabytes to prevent zip bombs. |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated list of allowed CORS origins for development. |

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health and liveness probe. Returns `{"status": "ok"}`. |
| `POST` | `/api/convert` | Upload `multipart/form-data` with one or more `files`. Returns an array of conversion results. |
| `POST` | `/api/convert-alt` | Re-run conversion on a specific file using the alternative engine (`converter="pymupdf4llm"`). |

### Example Response Payload (`/api/convert`)
```json
[
  {
    "id": "c9bf9e57-1685-4c89-bafb-ff5af830be8a",
    "filename": "lecture_01.pptx",
    "path": "week1/lecture_01.pptx",
    "source_type": "pptx",
    "status": "ok",
    "markdown": "# Week 1: Introduction\n\n- Key concepts...",
    "words": 420,
    "tokens_est": 560,
    "low_text": false,
    "error": null,
    "error_code": null,
    "converter": "markitdown",
    "retryable": false
  }
]
```

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
