"""
Pydantic Data Models (Schemas)
Author: Akshit Kumar Bansal
"""
from pydantic import BaseModel
from typing import Dict, Any

# ==========================================
# Authentication Models
# ==========================================
class UserCreate(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

# ==========================================
# PDF & AI Models
# ==========================================
class ChatRequest(BaseModel):
    sessionId: str
    query: str

class PodcastRequest(BaseModel):
    analysis_data: Dict[str, Any]
    language: str = "en"

class TranslateInsightsRequest(BaseModel):
    sessionId: str

class SelectionInsightsRequest(BaseModel):
    text: str