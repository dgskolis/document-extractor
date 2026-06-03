# GenHealth API

FastAPI backend for order management, document upload with LLM extraction, and request activity logging.

## Local setup

1. **Requirements:** Python 3.11+

2. **Create a virtual environment and install dependencies:**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. **Configure environment variables:**

```bash
cp .env.example .env
# Edit .env and set API_KEY and OPENAI_API_KEY (for document upload)
```

4. **Run the server:**

```bash
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. OpenAPI docs at `/docs`.

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_KEY` | Yes | — | Shared secret sent in the `X-API-Key` header for all `/api/v1/*` routes |
| `DATABASE_URL` | No | `sqlite:////tmp/orders.db` | SQLite database URL (must use `sqlite:///` scheme) |
| `OPENAI_API_KEY` | For upload | — | OpenAI API key for document patient-field extraction |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model name |
| `OPENAI_TIMEOUT_SECONDS` | No | `60` | Timeout for LLM requests (seconds) |
| `MAX_UPLOAD_SIZE_BYTES` | No | `26214400` | Max upload size for document endpoint (25 MB) |
| `MAX_DOCUMENT_TEXT_CHARS` | No | `100000` | Max characters of extracted document text sent to the LLM |
| `ACTIVITY_LOG_MAX_ENTRIES` | No | `10000` | Max activity log rows kept (oldest pruned on startup) |
| `APP_NAME` | No | `GenHealth API` | FastAPI application title |
| `DEBUG` | No | `false` | Enable debug mode |

**Railway note:** The default SQLite path (`/tmp/orders.db`) is writable on Railway but **ephemeral** — data is lost on redeploy. For production persistence, set `DATABASE_URL` to a mounted volume path or migrate to Postgres.

**SQLite concurrency:** Run uvicorn with a **single worker** (`--workers 1` or no `--workers` flag). SQLite does not handle concurrent writes well across multiple worker processes.

## Authentication

All `/api/v1/*` endpoints require the header:

```
X-API-Key: <your API_KEY value>
```

Health check routes (`/health`, `/health/ready`) are public and do not require an API key.

## Example curl commands

Set your base URL and API key:

```bash
export BASE_URL="http://127.0.0.1:8000"
export API_KEY="your-secret-key"
```

### Health (no API key)

```bash
curl "$BASE_URL/health"
curl "$BASE_URL/health/ready"
```

### Orders

```bash
# Create order
curl -X POST "$BASE_URL/api/v1/orders/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "patient_first_name": "Jane",
    "patient_last_name": "Doe",
    "date_of_birth": "1990-05-15"
  }'

# List orders
curl "$BASE_URL/api/v1/orders/?limit=10&offset=0" \
  -H "X-API-Key: $API_KEY"

# Get order by ID
curl "$BASE_URL/api/v1/orders/{order_id}" \
  -H "X-API-Key: $API_KEY"

# Update order
curl -X PUT "$BASE_URL/api/v1/orders/{order_id}" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"status": "in_progress"}'

# Delete order
curl -X DELETE "$BASE_URL/api/v1/orders/{order_id}" \
  -H "X-API-Key: $API_KEY"
```

### Upload document

```bash
curl -X POST "$BASE_URL/api/v1/orders/upload-document" \
  -H "X-API-Key: $API_KEY" \
  -F "file=@/path/to/document.pdf"
```

### Activity logs

```bash
curl "$BASE_URL/api/v1/logs/" \
  -H "X-API-Key: $API_KEY"
```

## Railway deployment

1. Create a new Railway service and set the **root directory** to `backend/`.
2. Add environment variables in the Railway dashboard (at minimum `API_KEY` and `OPENAI_API_KEY` if using document upload).
3. Railway uses the [`Procfile`](Procfile) to start the app:

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

4. Migrations run automatically on startup. Use `/health/ready` for readiness checks.

## Error responses

All errors return a consistent JSON shape:

```json
{"error": "Human-readable message"}
```

Validation failures return HTTP 422 with field-level messages joined in the `error` string. Partial document extraction failures also include an `extraction` object with any fields that were extracted.
