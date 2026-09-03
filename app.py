from fastapi import FastAPI, HTTPException
from models import ChatRequest, ChatResponse
from llm_client import ask
from fastapi.responses import StreamingResponse
from llm_client import ask_stream

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


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    return StreamingResponse(
        ask_stream(req.prompt),
        media_type="text/event-stream",
    )


class TicketRequest(BaseModel):
    message: str


@app.post("/extract-ticket", response_model=TicketExtraction)
async def extract_ticket(req: TicketRequest):
    try:
        return await extract_ticket_info(req.message)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
