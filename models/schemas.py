from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union

class GitHubData(BaseModel):
    """GitHub analysis data with scores for various aspects."""
    Technical_Skills: int = Field(..., ge=0, le=100, description="Technical skills score from 0-100")
    Reputation: int = Field(..., ge=0, le=100, description="Reputation score from 0-100")
    Activity: int = Field(..., ge=0, le=100, description="Activity score from 0-100")

class AnalysisRequest(BaseModel):
    """Request model for the analyze endpoint."""
    github: GitHubData
    resume: str = Field(..., min_length=1, description="Resume text content")
    
    class Config:
        json_schema_extra = {
            "example": {
                "github": {
                    "Technical_Skills": 85,
                    "Reputation": 72,
                    "Activity": 90
                },
                "resume": "Full stack developer with 5 years of experience in Python, React, and AWS..."
            }
        }

class ResumeAnalysis(BaseModel):
    """Resume analysis with summary and extracted keywords."""
    summary: str
    keywords: List[str]

class ResumeScore(BaseModel):
    """Score breakdown from resume analysis."""
    Technical_Skills: int = Field(..., ge=0, le=100)
    Reputation: int = Field(..., ge=0, le=100)
    Activity: int = Field(..., ge=0, le=100)
    summary: str
    keywords: List[str]

class GitHubScore(BaseModel):
    """GitHub score data."""
    Technical_Skills: int
    Reputation: int
    Activity: int

class AnalysisResponse(BaseModel):
    """Response model for the analyze endpoint."""
    trust_score: int = Field(..., ge=0, le=100, description="Overall trust score from 0-100")
    resume_analysis: ResumeAnalysis
    github_score: GitHubScore
    resume_score: ResumeScore
    
    class Config:
        json_schema_extra = {
            "example": {
                "trust_score": 83,
                "resume_analysis": {
                    "summary": "Experienced full stack developer with 5 years in Python, React, and AWS.",
                    "keywords": ["python", "react", "aws", "full stack", "javascript"]
                },
                "github_score": {
                    "Technical_Skills": 85,
                    "Reputation": 72,
                    "Activity": 90
                },
                "resume_score": {
                    "Technical_Skills": 80,
                    "Reputation": 75,
                    "Activity": 85,
                    "summary": "Experienced full stack developer with 5 years in Python, React, and AWS.",
                    "keywords": ["python", "react", "aws", "full stack", "javascript"]
                }
            }
        } 