from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re

class GenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500)
    max_length: int = Field(100, ge=20, le=500)
    temperature: float = Field(0.7, ge=0.1, le=2.0)
    top_p: float = Field(0.9, ge=0.1, le=1.0)
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, prompt, info):
        if re.search(r'[^\w\s\.,!?\-@#$%^&*()_+=:;\"\'<>/{}\[\]|\\~`]', prompt):
            raise ValueError('Prompt has invalid characters')
        
        words=prompt.split()
        if len(words)>3 and len(set(words))/len(words) <0.3:
            raise ValueError('Prompt has excessive repeatation')
        return prompt.strip()
        
    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, temperature):
        if temperature < 0.1 or temperature > 2.0:
            raise ValueError('Temperature must be between 0.1 and 2.0')
        return temperature

class GenerationResponse(BaseModel):
    generated_text: str
    prompt: str
    model_used: str
    processing_time: float

    @field_validator('generated_text')
    @classmethod
    def normalize_generated_text(cls, value: str):
        text = (value or "").strip()
        text = re.sub(r'^[^A-Za-z]+', '', text)
        if not text:
            return "."
        while text and text[-1] in ['!', '?', '…']:
            text = text[:-1].rstrip()
        if not text.endswith('.'):
            text = text + '.'
        if text and not text[0].isupper():
            text = text[0].upper() + text[1:]
        return text
