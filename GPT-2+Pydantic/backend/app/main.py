from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .models import GenerationRequest, GenerationResponse
from .gpt2_handler import generator
import time
import uvicorn

app=FastAPI(
    title='Fine-Tuned GPT-2 API',
    description='API for story generation using fine-tuned GPT-2 Model',
    version='1.0.0'
)

#CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
async def root():
    return {"message": "Fine-tuned GPT-2 API is running!"}

@app.get("/health")
async def health_check():
    return {"status":"healthy","model_loaded": generator.model is not None}

@app.post("/generate", response_model=GenerationResponse)
async def generate_text(request: GenerationRequest):
    try:
        generated_text, processing_time = generator.generate_text(
            prompt=request.prompt,
            max_length=request.max_length,
            temperature=request.temperature,
            top_p=request.top_p
        )
        
        return GenerationResponse(
            generated_text=generated_text,
            prompt=request.prompt,
            model_used="fine-tuned-gpt-2",
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


if __name__=="__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)