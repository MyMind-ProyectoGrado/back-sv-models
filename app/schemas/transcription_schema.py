from pydantic import BaseModel, Field, validator
from typing import Dict, Optional
from datetime import datetime

# Modelo Pydantic para el input del cuerpo
class TranscriptionInput(BaseModel):
    text: str
    
class Transcription(BaseModel):
    date: str
    time: str
    text: str = Field(..., min_length=1)  
    emotion: str = Field(..., min_length=1)  
    emotionProbabilities: Dict[str, float]  
    sentiment: str = Field(..., min_length=1)  
    sentimentProbabilities: Dict[str, float]  
    topic: Optional[str] = None 

    @validator("date")
    def validate_date_format(cls, v):
        """Validate that the date is in the correct format (e.g., ISO format)."""
        try:
            datetime.fromisoformat(v)  
        except ValueError:
            raise ValueError("Invalid date format, expected ISO format")
        return v
