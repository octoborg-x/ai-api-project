from fastapi import FastAPI, HTTPException
from models import ChatRequest, ChatResponse
from llm_client import ask

app = FastAPI(title="AI API Project")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        result = await ask(req.prompt)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
