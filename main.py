from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Mizpah ML API", description="Mock API for face recognition services")

class ScanRequest(BaseModel):
    image: str  # Base64 encoded image
    mode: str   # "passive" or "active"

class ProfileData(BaseModel):
    name: str
    type: str  # "medical", "watchlist", "missing"
    blood_type: Optional[str] = None
    allergies: Optional[List[str]] = None
    conditions: Optional[List[str]] = None
    emergency_contact: Optional[str] = None

class ScanResponse(BaseModel):
    matched: bool
    confidence: float
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
    Mock endpoint for scanning a face.
    Returns a fake matched profile.
    """
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
    Mock endpoint for enrolling a face.
    """
    return EnrollResponse(
        success=True,
        message="Face enrolled successfully.",
        embedding_id="mock-uuid-1234-5678"
    )

if __name__ == "__main__":
    import uvicorn
    # Run the mock server
    uvicorn.run(app, host="0.0.0.0", port=8000)
