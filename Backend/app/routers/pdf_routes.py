import os
import json
import time
import uuid
import logging
import fitz
import hashlib
from typing import List, Dict, Any

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Header
from fastapi.responses import FileResponse, JSONResponse

import azure.cognitiveservices.speech as speechsdk
import pyttsx3

# --- Updated Modular Imports ---
from app.models.schemas import ChatRequest, PodcastRequest, TranslateInsightsRequest, SelectionInsightsRequest
from app.services.ai_service import call_gemini_api, generate_connected_analysis
from app.services.redis_client import get_redis_client
from app.services.session_manager import (
    create_session, get_session, add_message_to_history, 
    get_all_sessions_metadata_for_user, update_session, get_user
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["PDF Intelligence"])

# ... (rest of your code stays exactly the same) ...

SESSION_FILES_DIR = "session_files"
os.makedirs(SESSION_FILES_DIR, exist_ok=True)

SUPPORTED_LANGUAGES = { "en": "English", "hi": "Hindi" }
AZURE_VOICE_MAP = { "en": "en-US-JennyNeural", "hi": "hi-IN-SwaraNeural" }

# --- Dependencies ---
async def get_current_user(
    authorization: str = Header(default=None), 
    x_microservice_key: str = Header(default=None, alias="x-microservice-key")
):
    # 1. SPRING BOOT ENTRANCE (Primary)
    # If React sends the logged-in user's email, we trust that Spring Boot 
    # already authenticated them. We return the email so FastAPI can save 
    # the PDFs in a folder named after this specific user!
    if authorization:
        return {"email": authorization, "name": "Spring Boot User"}

    # 2. VIP ENTRANCE (Fallback)
    expected_key = os.environ.get("MICROSERVICE_API_KEY", "my_super_secret_dashboard_key_123")
    if x_microservice_key == expected_key:
        return {"email": "microservice@dashboard.local", "name": "Dashboard System"}

    # 3. REJECTION
    raise HTTPException(status_code=401, detail="No authentication headers provided by frontend.")

# (I am omitting the TTS functions to save space, copy text_to_speech_azure and text_to_speech_offline here if you use them!)

# --- Endpoints ---
@router.post("/analyze/")
async def analyze_documents(files: List[UploadFile] = File(...), persona: str = Form(...), job_to_be_done: str = Form(...), sessionId: str = Form(None), current_user: dict = Depends(get_current_user)):
    user_email = current_user['email']
    user_files_dir = os.path.join(SESSION_FILES_DIR, user_email)
    os.makedirs(user_files_dir, exist_ok=True)
    
    context_parts = []
    processed_filenames = set()
    cached_analysis_result = None  # Store cache hit here
    
    redis = get_redis_client()
    
    for file in files:
        if file.filename in processed_filenames: continue
        try:
            file_bytes = await file.read()
            
            # 1. Generate a unique MD5 hash (Included persona for accuracy!)
            file_hash = hashlib.md5(file_bytes).hexdigest()
            cache_key = f"pdf_analysis:{file_hash}_{job_to_be_done}_{persona}"
            
            # 2. Check Redis for existing analysis
            cached_data = redis.get(cache_key)
            
            if cached_data:
                print(f"🚀 CACHE HIT! Returning instant insights for {file.filename}")
                cached_analysis_result = json.loads(cached_data)
                processed_filenames.add(file.filename)
                continue # Skip reading the PDF text

            # 3. If no cache, proceed with normal PDF reading
            file_location = os.path.join(user_files_dir, file.filename)
            with open(file_location, "wb+") as file_object: file_object.write(file_bytes)
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                for page_num, page in enumerate(doc, start=1):
                    context_parts.append(f"--- START OF PAGE {page_num} ---\n{page.get_text()}\n")
            processed_filenames.add(file.filename)
            
            # 4. Save a flag to cache the result later
            file.file_hash_for_cache = cache_key
            
        except Exception as e: 
            print(f"\n--- PDF PROCESSING ERROR ---")
            print(f"Failed on {file.filename}: {str(e)}")
            print(f"----------------------------\n")
            raise HTTPException(status_code=400, detail=f"Could not process file: {file.filename}")
        
    # --- LOGIC BRANCHING ---
    if cached_analysis_result and not context_parts:
        # We got everything we needed from the cache! No need to call Gemini.
        analysis_result = cached_analysis_result
    elif not context_parts:
        # No cache hit AND no text extracted = error.
        raise HTTPException(status_code=400, detail="No content available.")
    else:
        # We extracted new text, time to call Gemini!
        full_text_context = "\n".join(context_parts)
        analysis_result = await generate_connected_analysis(full_text_context, persona, job_to_be_done)
        
        # Save the new Gemini analysis to Redis for future cache hits
        for file in files:
            if hasattr(file, 'file_hash_for_cache'):
                redis.setex(file.file_hash_for_cache, 86400, json.dumps(analysis_result))
    
    # --- FINALIZE METADATA ---
    file_path_map = {filename: f"/session_files/{user_email}/{filename}" for filename in processed_filenames}
    analysis_result["metadata"] = {
        "input_documents": list(processed_filenames),
        "persona": persona,
        "job_to_be_done": job_to_be_done,
        "processing_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "file_path_map": file_path_map,
        "user_id": user_email
    }
    
    if sessionId:
        update_session(sessionId, analysis_result)
        current_session_id = sessionId
    else:
        current_session_id = create_session(analysis_result, user_email)
        
    return JSONResponse(content={"sessionId": current_session_id, "analysis": analysis_result})

@router.post("/chat/")
async def chat_with_documents(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    session_data = get_session(request.sessionId)
    if not session_data: raise HTTPException(status_code=404, detail="Chat session not found.")
    add_message_to_history(request.sessionId, {"role": "user", "content": request.query})
    prompt = f"Context: {json.dumps(session_data['analysis'])}\n\nHistory: {session_data['chat_history']}\n\nUser Query: {request.query}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response_json = await call_gemini_api(payload)
    bot_message = {"role": "bot", "content": response_json['candidates'][0]['content']['parts'][0]['text']}
    add_message_to_history(request.sessionId, bot_message)
    return JSONResponse(content=bot_message)

@router.get("/sessions/")
async def get_sessions_list(current_user: dict = Depends(get_current_user)):
    return JSONResponse(content=get_all_sessions_metadata_for_user(current_user['email']))

@router.get("/sessions/{session_id}")
async def get_session_details(session_id: str, current_user: dict = Depends(get_current_user)):
    session_data = get_session(session_id)
    if not session_data: raise HTTPException(status_code=404, detail="Session not found.")
    return JSONResponse(content=session_data)

@router.post("/translate-insights/")
async def translate_insights(request: TranslateInsightsRequest, current_user: dict = Depends(get_current_user)):
    session_data = get_session(request.sessionId)
    if not session_data: 
        raise HTTPException(status_code=404, detail="Session not found.")

    prompt = f"""
    You are an expert translator. Translate the following JSON insights into Hindi.
    Respond ONLY with a valid JSON object matching the exact original structure, but with all string values translated to Hindi.
    
    Original Insights:
    {json.dumps(session_data['analysis'])}
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    
    try:
        response_json = await call_gemini_api(payload)
        translated_insights = json.loads(response_json['candidates'][0]['content']['parts'][0]['text'])
        
        # Update the session with the new translated data
        session_data["translated_analysis"] = translated_insights
        update_session(request.sessionId, session_data)
        
        return JSONResponse(content={"translated_analysis": translated_insights})
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to translate insights: {e}")