from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Audio2txt Enterprise API",
    description="High-performance AI transcription and analysis API for professional services",
    version="4.0.0",
)

# Configure CORS for Web Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routers import transcription, vocabulary, auth, system
from .security import get_current_username

# 身分驗證路由
app.include_router(auth.router)

# 需驗證的 API
auth_dependency = Depends(get_current_username)
app.include_router(transcription.router, dependencies=[auth_dependency])
app.include_router(vocabulary.router, dependencies=[auth_dependency])
app.include_router(system.router, dependencies=[auth_dependency])

@app.get("/")
async def root():
    return {
        "system": "Audio2txt Enterprise",
        "version": "4.0.0",
        "status": "online",
        "cloud_provider": "AssemblyAI"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
