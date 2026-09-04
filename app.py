# third-party
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import APITimeoutError, RateLimitError, APIError

# local
from models import ChatRequest, ChatResponse, TicketExtraction
from llm_client import ask, ask_stream, extract_ticket_info

app = FastAPI(title="AI API Project")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        result = await ask(req.prompt)
        return ChatResponse(**result)
    except RateLimitError as e:
        raise HTTPException(
            status_code=429, detail="Rate limited by provider, try again shortly"
        ) from e
    except APITimeoutError as e:
        raise HTTPException(status_code=504, detail="LLM provider timed out") from e
    except APIError as e:
        raise HTTPException(
            status_code=502, detail=f"LLM provider error: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected error: {str(e)}"
        ) from e


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
        raise HTTPException(status_code=422, detail=str(e)) from e
