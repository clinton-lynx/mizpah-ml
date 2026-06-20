from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from core.config import supabase
from core.match import match_person
from core.enroll import enroll_person

# Increase MultiPartParser size limits globally to support larger webcam uploads
import starlette.formparsers
import starlette.multipartparser

starlette.formparsers.MultiPartParser.max_part_size = 100 * 1024 * 1024  # 100 MB
starlette.multipartparser.MultiPartParser.max_part_size = 100 * 1024 * 1024  # 100 MB

app = FastAPI(title="Mizpah ML API", description="Mock API for face recognition services")

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class MaxPartSizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
                # Cache the form data with a higher limit so FastAPI doesn't crash later
                try:
                    await request.form(max_parts=1000, max_part_size=100 * 1024 * 1024)
                except TypeError:
                    # In case the starlette version doesn't support these kwargs
                    await request.form()
        return await call_next(request)

app.add_middleware(MaxPartSizeMiddleware)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Mizpah ML API is running!"}

class ScanRequest(BaseModel):
    image: str  # Base64 encoded image
    mode: str   # "passive" or "active"

class ProfileData(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None  # "medical", "watchlist", "missing"
    person_id: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[List[str]] = None
    conditions: Optional[List[str]] = None
    emergency_contact: Optional[str] = None

class ScanResponse(BaseModel):
    matched: bool
    confidence: float
    distance: Optional[float] = None
    profile: Optional[ProfileData] = None

class EnrollRequest(BaseModel):
    image: str  # Base64 encoded image
    person_id: str
    type: str   # "medical", "watchlist", "missing"

class EnrollResponse(BaseModel):
    success: bool
    message: str
    embedding_id: Optional[str] = None

@app.post("/scan", response_model=ScanResponse)
def scan_face(request: ScanRequest):
    """
    Endpoint for scanning a face.
    If Supabase is configured, runs the real DeepFace match logic.
    Otherwise, falls back to a mock response.
    """
    if supabase is not None:
        try:
            result = match_person(request.image, request.mode)
            return ScanResponse(**result)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
    # Mock fallback
    if request.mode == "active":
        return ScanResponse(
            matched=True,
            confidence=98.5,
            profile=ProfileData(
                name="John Doe",
                type="medical",
                blood_type="O+",
                allergies=["Penicillin", "Peanuts"],
                conditions=["Asthma"],
                emergency_contact="+1234567890"
            )
        )
    else:
        return ScanResponse(
            matched=True,
            confidence=95.2,
            profile=ProfileData(
                name="Jane Doe",
                type="missing"
            )
        )

@app.post("/enroll", response_model=EnrollResponse)
def enroll_face(request: EnrollRequest):
    """
    Endpoint for enrolling a face.
    If Supabase is configured, runs the real DeepFace extraction logic.
    Otherwise, returns a mock success.
    """
    if supabase is not None:
        try:
            emb_id = enroll_person(request.image, request.person_id, request.type)
            return EnrollResponse(
                success=True,
                message="Face enrolled successfully via DeepFace.",
                embedding_id=str(emb_id)
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
    # Mock fallback
    return EnrollResponse(
        success=True,
        message="Face enrolled successfully.",
        embedding_id="mock-uuid-1234-5678"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
