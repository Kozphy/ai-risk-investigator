# AI Risk Investigator

Production-oriented SaaS for auditors, risk managers, compliance officers, and legal teams to upload contracts, policies, financial reports, and audit evidence — then receive evidence-backed AI risk findings, executive summaries, and downloadable audit reports.

> Demo mode ships with a deterministic mock LLM so the stack runs without API keys. Set `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` and `DEFAULT_LLM_PROVIDER` for live models (`gpt-4.1`, `gpt-5` when available on your account, or Claude).

## Features

- **Document upload** — PDF, DOCX, TXT
- **AI risk analysis** — compliance, operational, financial, legal, data privacy, vendor, AI governance
- **Risk scoring** — severity / probability / impact
- **Evidence extraction** — finding, explanation, supporting text, page number, confidence
- **RAG knowledge base** — regulations & frameworks (SOX, ISO 27001, COSO, GDPR, AI Act, SOPs)
- **Executive summary + heatmap**
- **Audit report export** — PDF and DOCX
- **Security** — JWT auth, RBAC, audit logs, rate limiting
- **Observability** — structured JSON logs, OpenTelemetry tracing

## Architecture

```mermaid
flowchart LR
  User[Web User] --> Next[Next.js 15 Frontend]
  Next --> API[FastAPI API]
  API --> Auth[JWT + RBAC]
  API --> Analyzer[Risk Analyzer]
  API --> RAG[RAG Store]
  API --> Reports[Report Generator]
  Analyzer --> LLM[OpenAI / Claude / Mock]
  RAG --> Embed[text-embedding-3-large or local demo vectors]
  RAG --> PG[(PostgreSQL + pgvector)]
  Analyzer --> PG
  Reports --> Files[(Report Files)]
  API --> Audit[Audit Logs]
```

## ER Diagram

```mermaid
erDiagram
  users ||--o{ documents : owns
  users ||--o{ analyses : creates
  users ||--o{ audit_logs : generates
  documents ||--o{ document_chunks : has
  documents ||--o{ analyses : analyzed_in
  analyses ||--o{ findings : produces
  analyses ||--o{ reports : exports
  knowledge_documents ||--o{ knowledge_chunks : embeds
```

## RAG Flow

```mermaid
sequenceDiagram
  participant U as User
  participant API as FastAPI
  participant Parse as Document Parser
  participant Emb as Embedding Service
  participant V as pgvector
  participant LLM as LLM Provider

  U->>API: Upload document
  API->>Parse: Extract text/pages
  Parse->>Emb: Chunk + embed document
  Emb->>V: Store document_chunks
  U->>API: Start analysis
  API->>V: Retrieve top-k knowledge chunks
  V-->>API: Framework excerpts
  API->>LLM: System prompt + KB + document excerpts
  LLM-->>API: JSON findings + executive summary
  API->>V: Persist findings
  U->>API: Export PDF/DOCX report
```

## Repository Layout

```
ai-risk-investigator/
├── backend/                 # FastAPI app
│   ├── app/
│   │   ├── api/             # HTTP routes
│   │   ├── analyzer/        # Risk analysis orchestration
│   │   ├── rag/             # Embeddings + retrieval
│   │   ├── reporting/       # PDF/DOCX generation
│   │   ├── services/        # Parser, LLM, storage, audit
│   │   ├── models/          # SQLAlchemy entities
│   │   └── schemas/         # Pydantic contracts
│   ├── alembic/             # Migrations
│   └── tests/
├── frontend/                # Next.js 15 + Tailwind + Recharts
├── docs/openapi.yaml
├── examples/                # Sample contract + KB excerpts + sample report
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## Quick Start (Docker)

```bash
cd ai-risk-investigator
cp .env.example .env
docker compose up --build
```

- Web: http://localhost:3000  
- API: http://localhost:8000  
- OpenAPI UI: http://localhost:8000/docs  
- Static OpenAPI: [docs/openapi.yaml](docs/openapi.yaml)

### First login

1. Open http://localhost:3000/login  
2. Register an account (first user becomes `admin`)  
3. Upload `examples/documents/sample_vendor_contract.txt`  
4. Review findings, then export a PDF from **Reports**

### Seed knowledge base (optional)

```bash
TOKEN=<access_token>
curl -X POST http://localhost:8000/api/v1/knowledge \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@examples/knowledge/gdpr_excerpt.txt" \
  -F "title=GDPR Excerpts" \
  -F "source_type=regulation" \
  -F "framework=GDPR"
```

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
# start Postgres with pgvector, then:
alembic upgrade head
uvicorn app.main:app --reload --port 8000
pytest -q
```

### Frontend

```bash
cd frontend
npm install
echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local
npm run dev
```

## Configuration

| Variable | Purpose |
|----------|---------|
| `DEFAULT_LLM_PROVIDER` | `openai` \| `anthropic` \| `mock` |
| `OPENAI_MODEL` | e.g. `gpt-4.1` or `gpt-5` |
| `ANTHROPIC_MODEL` | Claude model id |
| `EMBEDDING_MODEL` | `text-embedding-3-large` |
| `DEMO_MODE` | Use mock LLM / local embeddings when keys absent |
| `JWT_SECRET_KEY` | **Required** strong secret in production |

## Security Model

| Role | Capabilities |
|------|----------------|
| `viewer` | Read findings/dashboard |
| `compliance` | + upload knowledge base |
| `risk_manager` / `auditor` | + upload docs, run analysis, export reports |
| `admin` | Full access |

All mutating actions write to `audit_logs` with user, IP, and user-agent.

## Testing

- Backend: `pytest` (parser, security, mock LLM, health)
- Frontend e2e: Playwright (`npm run test:e2e` with app running)
- CI: GitHub Actions builds frontend and runs backend unit tests

## Production Notes

1. Rotate `JWT_SECRET_KEY`; disable weak defaults  
2. Set `APP_ENV=production`, `DEMO_MODE=false`, real LLM keys  
3. Put object storage in front of `/data` volumes (S3/MinIO) for multi-instance  
4. Add managed Postgres with pgvector; tune IVFFlat/HNSW after data volume exists  
5. Terminate TLS at reverse proxy; restrict CORS  
6. Human review is mandatory — LLM findings are decision support, not legal opinions

## License

MIT — see project use constraints for your organization.
