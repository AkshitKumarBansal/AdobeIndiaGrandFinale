import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv

# Import our new modular routers
from app.routers import auth_routes, pdf_routes
from app.services.redis_client import get_redis_client

from app.core.database import engine, Base
from app.models.user import User

load_dotenv()
logging.basicConfig(level=logging.INFO)

Base.metadata.create_all(bind=engine)

# --- Initialize FastAPI App ---
app = FastAPI(
    title="PDF Intelligence API",
    description="Microservice API for PDF analysis.",
    version="3.3.0"
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "http://localhost:5173", "https://auth-frontend-a6x9.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    get_redis_client()
    if not os.environ.get("GOOGLE_API_KEY"):
        print("CRITICAL WARNING: GOOGLE_API_KEY is not set!")
    print("Application startup complete.")

# --- Register Routers ---
app.include_router(auth_routes.router)
app.include_router(pdf_routes.router)

# --- React Static Files & Catch-all Route ---
SESSION_FILES_DIR = "session_files"
os.makedirs(SESSION_FILES_DIR, exist_ok=True)
app.mount("/session_files", StaticFiles(directory=SESSION_FILES_DIR), name="session_files")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_BUILD_DIR = os.path.join(BASE_DIR, "..", "Frontend", "build")
STATIC_DIR = os.path.join(FRONTEND_BUILD_DIR, "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    file_path = os.path.join(FRONTEND_BUILD_DIR, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path): return FileResponse(file_path)
    index_path = os.path.join(FRONTEND_BUILD_DIR, "index.html")
    if os.path.exists(index_path): return FileResponse(index_path)
    return JSONResponse(status_code=404, content={"error": "Standalone frontend not built."})

@app.get("/")
def read_root():
    index_path = os.path.join(FRONTEND_BUILD_DIR, "index.html")
    if os.path.exists(index_path): return FileResponse(index_path)
    return {"status": "ok", "mode": "Microservice Active"}