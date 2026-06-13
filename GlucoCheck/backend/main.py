from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routes import auth_router, chat_router, sessions_router, upload_router
from database import init_db
import os

app = FastAPI(
    title="GlucoCheck API",
    description="Smart Diabetes Diagnosis Agent — Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,     prefix="/api")
app.include_router(chat_router,     prefix="/api")
app.include_router(sessions_router, prefix="/api")
app.include_router(upload_router,   prefix="/api")

# خدمة الملفات المرفوعة محلياً
uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/")
async def root():
    return {"message": "GlucoCheck API is running", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
