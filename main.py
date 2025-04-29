from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from agents.github import analyze_github
from agents.resume import analyze_resume
from utils.score import calculate_trust_score
from utils.logging.logger import log
import os
from dotenv import load_dotenv
from models.schemas import AnalysisRequest, AnalysisResponse, ResumeAnalysis

# Load environment variables
load_dotenv()

# Configuration flags
use_mock = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

# Check if API keys are set
has_openai_key = bool(os.getenv("OPENAI_API_KEY"))
has_deepseek_key = bool(os.getenv("DEEPSEEK_API_KEY"))
has_openrouter_key = bool(os.getenv("OPENROUTER_API_KEY"))

if not has_openai_key and not has_deepseek_key and not has_openrouter_key and not use_mock:
    log.error("No API keys found. Please set one of: OPENAI_API_KEY, DEEPSEEK_API_KEY, OPENROUTER_API_KEY or USE_MOCK_DATA=true")
    print("Error: No API keys found. Set one of: OPENAI_API_KEY, DEEPSEEK_API_KEY, OPENROUTER_API_KEY or USE_MOCK_DATA=true in your .env file.")

# Initialize FastAPI app
app = FastAPI(
    title="TrustScore AI API",
    description="API for analyzing GitHub profiles and resumes to calculate trust scores for recruitment",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """Health check endpoint"""
    config_info = {
        "mock_mode": use_mock,
        "openrouter_configured": has_openrouter_key,
        "deepseek_configured": has_deepseek_key,
        "openai_configured": has_openai_key
    }
    return {
        "status": "ok", 
        "message": "Welcome to TrustScore AI API",
        "config": config_info
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """
    Analyze GitHub profile and resume to calculate a trust score.
    
    This endpoint processes GitHub data and resume text to generate
    a comprehensive trust score along with detailed analysis.
    """
    try:
        log.info("Starting analysis for new request")
        
        github_data = request.github.dict()
        resume_text = request.resume
        
        # Perform analyses
        github_score = analyze_github(github_data)
        resume_score = analyze_resume(resume_text)
        
        # Extract resume analysis
        resume_analysis = ResumeAnalysis(
            summary=resume_score.get("summary", "No summary available"),
            keywords=resume_score.get("keywords", [])
        )
        
        # Calculate trust score
        trust_score = calculate_trust_score(github_score, resume_score)
        
        # Construct response
        result = AnalysisResponse(
            trust_score=trust_score,
            resume_analysis=resume_analysis,
            github_score=github_score,
            resume_score=resume_score
        )
        
        log.info(f"Analysis completed successfully with trust score: {trust_score}")
        return result
        
    except Exception as e:
        log.error(f"Error during analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
