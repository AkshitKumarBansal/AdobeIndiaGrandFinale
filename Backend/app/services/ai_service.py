"""
AI Engine Service
Author: Akshit Kumar Bansal
"""
import os
import json
import logging
import asyncio
import random
import httpx
from typing import Dict, Any
from fastapi import HTTPException

import google.auth
import google.auth.transport.requests

# Initialize the logger for this specific file
logger = logging.getLogger(__name__)

# ==============================================================================
# AI Helper Functions
# ==============================================================================
async def call_gemini_api(payload: dict, timeout: float = 120.0) -> dict:
    model = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash").strip()
    api_key = os.environ.get("GOOGLE_API_KEY")

    if api_key:
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key.strip()}"
        headers = {"Content-Type": "application/json"}
    else:
        creds, _ = google.auth.load_credentials_from_file(
            os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        auth_req = google.auth.transport.requests.Request()
        creds.refresh(auth_req)
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}

    max_retries = 5
    base_wait_time = 1
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(api_url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            error_body = e.response.text 
            print(f"\n--- GOOGLE API ERROR ---\n{error_body}\n------------------------\n")
            if e.response.status_code in (429, 503):
                wait_time = (base_wait_time * (2 ** attempt)) + random.uniform(0, 1)
                logger.warning(f"Gemini error {e.response.status_code}. Retrying in {wait_time:.2f}s...")
                await asyncio.sleep(wait_time)
                continue
            raise HTTPException(status_code=e.response.status_code, detail=f"Gemini API rejected request: {error_body}")
        except (httpx.ReadTimeout, httpx.RequestError) as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
                continue
            raise HTTPException(status_code=504, detail=f"Gemini request failed: {e}")
    raise HTTPException(status_code=503, detail="Gemini API unavailable after retries.")


async def generate_connected_analysis(full_text_context: str, persona: str, job_to_be_done: str) -> Dict[str, Any]:
    json_schema_string = """
    {
        "top_sections": [
            {
                "importance_rank": 1,
                "document": "filename.pdf",
                "page_number": 3,
                "section_title": "Section Name",
                "subsection_analysis": "Snippet...",
                "reasoning": "Why this matters..."
            }
        ],
        "llm_insights": {
            "key_insights": ["insight 1", "insight 2"],
            "did_you_know": ["fact 1", "fact 2"],
            "cross_document_connections": ["connection 1", "connection 2"]
        }
    }
    """
    prompt = f"""
    You are an expert research assistant acting as a '{persona}' whose goal is to '{job_to_be_done}'.
    Analyze the provided context, which contains the full text from one or more documents.
    
    *Your Reasoning Process:*
    1. *Assess Relevance:* Review the user's goal. Read through all document texts and decide which are relevant.
    2. *Extract Initial Insights:* Extract the top 5 most important sections that directly address the user's goal. Include the page number exactly as it appears in the context markers.
    3. *Synthesize Connected Insights:* Find connections, patterns, or contradictions.
    *Provided Context:*
    {full_text_context}
    *Instructions:*
    Respond ONLY with a valid JSON object matching this exact structure, with no markdown formatting or backticks:
    {json_schema_string}
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}],"generationConfig": {"responseMimeType": "application/json"}}
    try:
        response_json = await call_gemini_api(payload)
        return json.loads(response_json['candidates'][0]['content']['parts'][0]['text'])
    except Exception as e:
        logger.error(f"Failed to generate connected analysis: {e}")
        return {"top_sections": [],"llm_insights": {"key_insights": [f"Error during analysis: {e}"],"did_you_know": [],"cross_document_connections": ["Could not establish connections due to an error."]}}