## Commands reference

## Notes
- Always activate venv (`source venv/bin/activate`) before running
  `uvicorn` — forgetting this causes `ModuleNotFoundError`.

## Endpoints
- `GET /health` — health check
- `POST /chat` — single-turn chat, returns full response + token usage
- `POST /chat/stream` — streaming chat response (SSE-style)
- `POST /extract-ticket` — extracts structured data (category, urgency,
  sentiment) from a support message, validated against a fixed schema

### Setup
\`\`\`bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
\`\`\`

### Run the API server
\`\`\`bash
source venv/bin/activate
uvicorn app:app --reload
\`\`\`
Server runs at http://localhost:8000
Interactive docs: http://localhost:8000/docs

### Run the CLI test script
\`\`\`bash
source venv/bin/activate
python main.py
\`\`\`

### Test endpoints
\`\`\`bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "hi"}'
\`\`\`

