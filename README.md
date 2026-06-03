# GenHealth

GenHealth is an order management app for healthcare workflows. Upload patient documents (PDFs and images), extract patient details with OCR and an LLM, create and manage orders, and review API activity logs.

The repo is split into a **FastAPI backend** and a **React frontend**.

## Features

- **Orders** — Create, list, view, update, and delete patient orders
- **Document upload** — Upload PDFs or images; text is extracted directly or via Tesseract OCR for scanned documents
- **LLM extraction** — OpenAI extracts patient name and date of birth from document text
- **Manual entry** — Create orders by hand or pre-fill the form from extracted data
- **Activity logging** — API requests are logged for auditing and debugging
- **Health checks** — Public `/health` and `/health/ready` endpoints

## Tech stack

| Layer | Stack |
|-------|-------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy, Alembic, SQLite, LangChain + OpenAI |
| Frontend | React 19, TypeScript, Vite, TanStack Query, React Router, Tailwind CSS |
| OCR | Tesseract (via `pytesseract`) |

## Project structure

```
genhealth/
├── backend/          # FastAPI API, services, migrations, tests
│   ├── app/          # Application code
│   ├── alembic/      # Database migrations
│   └── tests/        # pytest suite
└── frontend/         # React SPA
    └── src/          # Pages, components, API client
```

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- **Tesseract** (required for OCR on scanned PDFs): `brew install tesseract` on macOS
- **OpenAI API key** (required for document upload / LLM extraction)

## Local setup

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` and set at minimum:

- `API_KEY` — shared secret used by the frontend and API clients
- `OPENAI_API_KEY` — your OpenAI key (needed for document upload)

Start the API:

```bash
uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`. OpenAPI docs are at `/docs`.

Database migrations run automatically on startup. By default, data is stored in `/tmp/orders.db`.

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env
```

Edit `frontend/.env`:

```bash
VITE_API_URL=http://localhost:8000
VITE_API_KEY=<same value as backend API_KEY>
```

Start the dev server:

```bash
npm run dev
```

Open the URL shown in the terminal (typically `http://localhost:5173`).

## Testing locally

### Backend (automated tests)

From `backend/` with the virtual environment activated:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing
```

Tests use an in-memory SQLite database and mock external services (OpenAI, OCR, etc.), so they do not require a running server or real API keys.

Test modules cover orders, document upload, auth, config validation, database migrations, exception handlers, activity logging, and schemas.

### Frontend

There is no frontend test suite yet. You can verify the build and lint locally:

```bash
cd frontend
npm run lint
npm run build
```

### End-to-end manual testing

1. Start the backend (`uvicorn app.main:app --reload`).
2. Start the frontend (`npm run dev`).
3. Confirm `VITE_API_KEY` matches `API_KEY` in the backend `.env`.
4. Visit the app and try:
   - **Orders** (`/`) — list, open order details, create via upload flow
   - **Upload** (`/upload`) — upload a PDF, review extracted fields, submit a manual or pre-filled order

Quick API smoke test without the UI:

```bash
export BASE_URL="http://127.0.0.1:8000"
export API_KEY="your-secret-key"

curl "$BASE_URL/health"
curl "$BASE_URL/api/v1/orders/" -H "X-API-Key: $API_KEY"
```

For document upload testing, set `OPENAI_API_KEY` in the backend `.env`. For scanned PDFs, ensure Tesseract is installed (`tesseract --version`).

More API examples (curl commands, error shapes) are in [backend/README.md](backend/README.md).

## Environment variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `API_KEY` | Yes | Shared secret for `X-API-Key` header |
| `OPENAI_API_KEY` | For upload | OpenAI key for patient-field extraction |
| `DATABASE_URL` | No | SQLite URL (default: `sqlite:////tmp/orders.db`) |
| `TESSERACT_CMD` | No | Path to Tesseract if not on `PATH` |

See [backend/.env.example](backend/.env.example) and [backend/README.md](backend/README.md) for the full list.

### Frontend (`frontend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes | Backend URL, no trailing slash |
| `VITE_API_KEY` | Yes | Must match backend `API_KEY` |

## Deployment

| Component | Platform | Root directory |
|-----------|----------|----------------|
| Backend | [Railway](https://railway.app) | `backend/` |
| Frontend | [Vercel](https://vercel.com) | `frontend/` |

Set the same env vars in each platform as in local `.env` files. Point `VITE_API_URL` at your deployed backend URL and redeploy the frontend after changing it (Vite bakes env vars in at build time).

See [backend/README.md](backend/README.md#railway-deployment) for Railway-specific notes (Tesseract, SQLite persistence, single worker).
