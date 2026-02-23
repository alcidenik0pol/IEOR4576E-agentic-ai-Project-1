"""
FastAPI application for HuggingFace Models Explorer.

Provides:
- POST /chat - Main question answering endpoint
- GET /health - Health check
- GET / - Serve static frontend
"""

import json
import re
from contextlib import asynccontextmanager
from pathlib import Path

import vertexai
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from vertexai.generative_models import GenerativeModel, GenerationConfig

from app.backstop import check_out_of_scope, check_intent_with_llm
from app.config import get_settings
from app.middleware import SecurityHeadersMiddleware, RequestLoggingMiddleware, setup_cors
from app.models import ChatRequest, ChatResponse, HealthResponse
from app.prompts import format_chat_prompt

# Configuration
settings = get_settings()
DATA_FILE = Path(__file__).parent.parent / "data" / "models_snapshot_20260221.json"
STATIC_DIR = Path(__file__).parent.parent / "static"

# Rate limiter setup (in-memory, per-instance)
# Note: No default_limits - we apply limits explicitly per-endpoint
limiter = Limiter(key_func=get_remote_address)

# Global state
models_data: list[dict] = []
snapshot_date: str = ""
llm_model: GenerativeModel | None = None


def load_model_data() -> tuple[list[dict], str]:
    """Load model data from frozen JSON snapshot."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_FILE}")

    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    return data["models"], data["snapshot_date"][:10]


def extract_source_models(answer: str) -> list[str]:
    """Extract model IDs mentioned in the answer."""
    # Pattern matches typical HF model IDs: org/model-name
    pattern = r"\b([a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+)\b"
    matches = re.findall(pattern, answer)

    # Filter to only known models
    known_ids = {m["model_id"] for m in models_data}
    return [m for m in matches if m in known_ids]


def estimate_confidence(answer: str, sources: list[str], out_of_scope: bool) -> float:
    """
    Estimate confidence based on answer characteristics.

    This is a heuristic - real confidence would come from the LLM.
    """
    if out_of_scope:
        return 1.0  # We're confident it's out of scope

    # Base confidence
    confidence = 0.7

    # Boost if we cited sources
    if sources:
        confidence += 0.1 * min(len(sources), 3)

    # Boost for specific numbers (downloads, parameters)
    if re.search(r"\d+[MBK]?\+?", answer):
        confidence += 0.1

    # Reduce for uncertainty markers
    uncertainty_phrases = ["i'm not sure", "might be", "possibly", "likely", "approximately"]
    for phrase in uncertainty_phrases:
        if phrase in answer.lower():
            confidence -= 0.1
            break

    return min(max(confidence, 0.0), 1.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize on startup."""
    global models_data, snapshot_date, llm_model

    # Load model data
    models_data, snapshot_date = load_model_data()
    print(f"Loaded {len(models_data)} models (snapshot: {snapshot_date})")

    # Initialize Vertex AI using Application Default Credentials
    # Cloud Run automatically provides ADC via the compute service account
    try:
        vertexai.init(
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )
        llm_model = GenerativeModel(settings.vertex_model_id)
        print(f"Initialized Vertex AI with model: {settings.vertex_model_id}")
    except Exception as e:
        print(f"Warning: Could not initialize Vertex AI: {e}")
        llm_model = None

    yield

    # Cleanup (if needed)
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="HuggingFace Models Explorer",
    description="Q&A chatbot for the top 100 HuggingFace models",
    version="0.1.0",
    lifespan=lifespan,
)

# Store limiter in app state for slowapi
app.state.limiter = limiter


# Rate limit exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return a 429 response when rate limit is exceeded."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please wait before making more requests.",
            "retry_after": exc.detail,
        },
    )


# Setup middleware (order matters - last added is first executed)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
setup_cors(app)


# Exempt health endpoint from rate limiting by checking path
@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint (exempt from rate limiting)."""
    return HealthResponse(
        status="ok",
        model_count=len(models_data),
        snapshot_date=snapshot_date,
        llm_available=llm_model is not None,
    )


@app.post("/chat", response_model=ChatResponse)
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_period}")
async def chat(request: Request, chat_request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint for asking questions about HuggingFace models.

    The flow:
    1. Check regex-based out-of-scope backstop (fast)
    2. Check LLM-based intent classifier (catches creative attacks)
    3. Generate response using Vertex AI
    4. Extract sources and estimate confidence
    """
    question = chat_request.question.strip()

    # Step 1: Check regex-based out-of-scope
    is_oos, oos_response = check_out_of_scope(question)
    if is_oos:
        return ChatResponse(
            answer=oos_response,
            confidence=1.0,
            sources=[],
            out_of_scope=True,
        )

    # Step 2: Check LLM intent classifier
    if llm_model is None:
        raise HTTPException(
            status_code=503,
            detail="LLM model not available. Check Vertex AI configuration.",
        )

    is_safe, malicious_response = check_intent_with_llm(question, llm_model)
    if not is_safe:
        return ChatResponse(
            answer=malicious_response,
            confidence=1.0,
            sources=[],
            out_of_scope=True,
        )

    # Step 3: Generate response
    try:
        # Build prompt with context
        prompt = format_chat_prompt(question, models_data)

        # Configure generation
        config = GenerationConfig(
            temperature=0.3,  # Lower for factual responses
            max_output_tokens=1024,
        )

        # Generate response
        response = llm_model.generate_content(prompt, generation_config=config)
        answer = response.text

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}",
        )

    # Step 4: Post-process response
    sources = extract_source_models(answer)
    confidence = estimate_confidence(answer, sources, False)

    return ChatResponse(
        answer=answer,
        confidence=confidence,
        sources=sources,
        out_of_scope=False,
    )


@app.get("/", response_model=None)
async def serve_frontend() -> FileResponse | JSONResponse:
    """Serve the frontend HTML."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return JSONResponse(
        {"message": "HuggingFace Models Explorer API. Use POST /chat to ask questions."},
    )


# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
