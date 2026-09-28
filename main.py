"""
UDO AI Service - Google Cloud Run Entry Point
FastAPI application connecting Vertex AI / Gemini with UDO Welding Knowledge Base.
Strict rule: Absolutely NO emojis in source code, comments, logs, or output.
"""

import os
import json
from typing import Optional
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from knowledge import UdoCatalogKnowledge

# Initialize Knowledge Base
knowledge = UdoCatalogKnowledge()

# Configuration
GCP_PROJECT = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT") or "project-de5847cd-022d-40ca-ad7"
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "global")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

app = FastAPI(
    title="UDO AI Overview Service",
    description="Vertex AI & Gemini Search Service for UDO E-Commerce",
    version="1.0.0"
)

# CORS Middleware allowing frontend and PHP server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    q: str
    top_k: Optional[int] = 8

@app.get("/")
def read_root():
    return {
        "status": "ok",
        "service": "UDO AI Overview Service",
        "model": MODEL_NAME,
        "vertex_ai_configured": bool(GCP_PROJECT),
        "api_key_configured": bool(GEMINI_API_KEY)
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

def build_system_instruction(retrieved_context: str) -> str:
    return (
        "You are UDO AI, an expert industrial welding and hardware advisor for UDO (บริษัท ยู.ดี.โอ. เทรดดิ้ง จำกัด), "
        "Thailand's premier distributor of welding wires, welding machines, and industrial tools. "
        "Your task is to generate a comprehensive, articulate, and well-structured Thai response matching Google AI Overview style.\n\n"
        "STRICT CONSTRAINTS:\n"
        "1. Absolutely NO emojis anywhere in the response text or attributes.\n"
        "2. Ground your recommendations on the following authentic UDO products whenever relevant:\n"
        f"{retrieved_context}\n\n"
        "3. Respond strictly in valid JSON matching this exact structure:\n"
        "{\n"
        '  "lead": {\n'
        '    "keyword": "string - Key product category or welding process",\n'
        '    "highlight": "string - Core defining attribute or main specification",\n'
        '    "summary": "string - Clear practical explanation of what it is used for",\n'
        '    "badge": {"type": "udo", "text": "UDO ช็อป +1", "brand": "Brand Name"}\n'
        "  },\n"
        '  "sections": [\n'
        '    {\n'
        '      "title": "string - Descriptive section heading",\n'
        '      "items": [\n'
        '        {\n'
        '          "title": "string - Item title or model name (optional)",\n'
        '          "desc": "string - Detailed explanation with technical specs",\n'
        '          "badge": {"type": "udo", "text": "UDO · สต็อกพร้อมส่ง", "brand": "Brand Name"}\n'
        '        }\n'
        '      ]\n'
        '    }\n'
        '  ],\n'
        '  "followUps": [\n'
        '    "string - Follow-up clarification question 1",\n'
        '    "string - Follow-up clarification question 2",\n'
        '    "string - Follow-up clarification question 3"\n'
        '  ],\n'
        '  "citations": [\n'
        '    {\n'
        '      "brand": "Brand Name",\n'
        '      "source": "Global House / UDO Knowledge / Thai Watsadu",\n'
        '      "title": "Document or Guide Title",\n'
        '      "desc": "Short snippet describing the source...",\n'
        '      "image": "/images/brands/welpro.png",\n'
        '      "initial": "G",\n'
        '      "bg": "#1b5e20"\n'
        '    }\n'
        '  ],\n'
        '  "relatedProductFilter": "string - Keyword to filter products in catalog shelf"\n'
        "}"
    )

def query_gemini_api(query: str, system_prompt: str) -> Optional[dict]:
    """
    Call Gemini via google-genai Client on Vertex AI (location='global').
    Preserves original system instruction and JSON schema completely.
    """
    try:
        from google import genai
        from google.genai import types

        client = None
        if GCP_PROJECT:
            client = genai.Client(vertexai=True, project=GCP_PROJECT, location=VERTEX_LOCATION)
        elif GEMINI_API_KEY:
            client = genai.Client(api_key=GEMINI_API_KEY)

        if client:
            config_kwargs = {
                "system_instruction": system_prompt,
                "response_mime_type": "application/json",
                "temperature": 0.25,
            }
            if "thinking" in MODEL_NAME.lower():
                config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=-1)

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=f"ให้ข้อมูลสรุปภาพรวมเกี่ยวกับ: {query} โดยละเอียด อธิบายเข้าใจง่าย ถูกต้องตามหลักการทางวิศวกรรมงานเชื่อม",
                config=types.GenerateContentConfig(**config_kwargs)
            )

            result_text = response.text or "{}"
            result_text = result_text.strip()
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

            parsed = json.loads(result_text.strip(), strict=False)
            if isinstance(parsed, dict):
                return parsed
            elif isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict):
                return parsed[0]
    except Exception as e:
        print(f"Error calling Gemini with google-genai: {e}")

    return None

def generate_grounded_fallback(query: str, products: list) -> dict:
    """
    High-quality grounded fallback using retrieved UDO catalog data.
    """
    q_lower = query.lower()
    main_brand = products[0].get("brand", "UDO") if products else "UDO"
    first_name = products[0].get("name", query) if products else query
    
    sections = []
    if products:
        items = []
        for p in products[:4]:
            std = ", ".join(p.get("standards", [])) if p.get("standards") else "มาตรฐานสากล"
            items.append({
                "title": f"{p.get('brand')} {p.get('name')}",
                "desc": f"รหัส {p.get('sku')} รองรับกระบวนการ {p.get('process')} สำหรับ{p.get('material')} มาตรฐาน {std} {p.get('snippet')}",
                "badge": {"type": "udo", "text": "UDO · สต็อกพร้อมส่ง", "brand": p.get("brand", "UDO")}
            })
        sections.append({
            "title": f"สินค้าและรุ่นแนะนำสำหรับ {query}",
            "items": items
        })

    sections.append({
        "title": "ข้อกำหนดและลักษณะทั่วไป",
        "items": [
            {"desc": "มีให้เลือกทั้งแบบม้วนและแบบแพ็ก พร้อมส่งตรงจากคลังสินค้า UDO ทั่วประเทศ"},
            {"desc": "ผ่านการรับรองคุณภาพมาตรฐานอุตสาหกรรมสากล ปลอดภัย แนวเชื่อมเรียบเนียน", "badge": {"type": "standard", "text": "AWS +4"}}
        ]
    })

    return {
        "query": query,
        "lead": {
            "keyword": query,
            "highlight": f"ผลิตภัณฑ์คุณภาพสูงจากตัวแทนจำหน่ายทางการ ({main_brand})",
            "summary": "ได้รับความนิยมสูงสุดในงานโครงสร้าง งานซ่อมบำรุง และงานอุตสาหกรรมประกอบโลหะ",
            "badge": {"type": "udo", "text": "UDO ช็อป +1", "brand": main_brand}
        },
        "sections": sections,
        "followUps": [
            f"คุณกำลังใช้งาน {query} ในงานลักษณะใด (โครงสร้างทั่วไป, งานโรงงาน, หรืองาน DIY)",
            "ต้องการความหนาหรือขนาดเส้นผ่านศูนย์กลางเท่าไหร่",
            "ต้องการใบรับรองสเปก Certificate หรือไม่"
        ],
        "citations": [
            {
                "brand": main_brand,
                "source": "UDO Knowledge Base",
                "title": f"คู่มือการใช้งานและคำแนะนำเทคนิคเกี่ยวกับ {query}",
                "desc": "รวมข้อแนะนำจากทีมช่างเทคนิค UDO วิเคราะห์แนวเชื่อม การปรับกระแสไฟ และการเลือกขนาดลวด...",
                "image": "/images/brands/welpro.png",
                "initial": "U",
                "bg": "#E7151A"
            },
            {
                "brand": "KOBELCO",
                "source": "Global House",
                "title": "มาตรฐานลวดเชื่อมและอุปกรณ์เชื่อมโลหะชั้นนำระดับสากล",
                "desc": "ข้อมูลความรู้เปรียบเทียบเกรดและคุณสมบัติทางกลของเนื้อโลหะเชื่อม...",
                "image": "/images/brands/welpro.png",
                "initial": "G",
                "bg": "#1b5e20"
            }
        ],
        "relatedProductFilter": query
    }

@app.get("/api/ai-search")
@app.post("/api/ai-search")
async def ai_search(request: Request, q: Optional[str] = Query(None)):
    query_str = q
    if not query_str and request.method == "POST":
        try:
            body = await request.json()
            query_str = body.get("q")
        except Exception:
            pass

    if not query_str or not query_str.strip():
        raise HTTPException(status_code=400, detail="Search query 'q' cannot be empty.")

    query_str = query_str.strip()[:200]

    # 1. Retrieve UDO Grounded Products
    retrieved_products = knowledge.retrieve_context(query_str, top_k=8)
    context_text = knowledge.format_context_for_prompt(retrieved_products)

    # 2. Call Gemini / Vertex AI
    system_prompt = build_system_instruction(context_text)
    gemini_data = query_gemini_api(query_str, system_prompt)

    if gemini_data and isinstance(gemini_data, dict):
        gemini_data["query"] = query_str
        return {
            "success": True,
            "source": "vertex_ai",
            "data": gemini_data
        }

    # 3. Fallback to Grounded Catalog
    fallback_data = generate_grounded_fallback(query_str, retrieved_products)
    return {
        "success": True,
        "source": "grounded_catalog",
        "data": fallback_data
    }
