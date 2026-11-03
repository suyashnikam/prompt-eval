import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from prompt_scorer import score_prompt

logger = logging.getLogger(__name__)

app = FastAPI(title="Prompt Scorer")
templates = Jinja2Templates(directory="templates")


class ScoreRequest(BaseModel):
    prompt: str = Field(max_length=20000)


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/api/score")
async def api_score(payload: ScoreRequest):
    prompt = payload.prompt.strip()
    if not prompt:
        return JSONResponse({"error": "Please paste a prompt to score."}, status_code=400)

    try:
        result = score_prompt(prompt)
    except Exception:
        # Log the full error server-side; it can contain AWS account/role details.
        logger.exception("Scoring failed")
        return JSONResponse({"error": "Scoring failed, please try again."}, status_code=500)

    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=5050, reload=True)
