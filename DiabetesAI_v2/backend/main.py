"""
DiabetesAI — FastAPI Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import auth_router, chat_router, sessions_router, upload_router
from database import init_db

app = FastAPI(
    title="DiabetesAI API",
    description="Smart Diabetes Diagnosis Agent — Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ─── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ────────────────────────────────────────────────────────────────────
app.include_router(auth_router,     prefix="/api")
app.include_router(chat_router,     prefix="/api")
app.include_router(sessions_router, prefix="/api")
app.include_router(upload_router,   prefix="/api")


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/")
async def root():
    return {"message": "DiabetesAI API is running ✓", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
