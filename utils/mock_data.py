"""
Mock data provider for testing without using external APIs.
This is useful when API keys are not available, have insufficient credits, 
or when running tests that shouldn't make actual API calls.
"""

import random
from typing import Dict, Any, List

def get_mock_github_score() -> Dict[str, Any]:
    """
    Generate mock GitHub analysis scores.
    
    Returns:
        Dict with scores for technical skills, reputation, and activity
    """
    return {
        "Technical_Skills": random.randint(65, 95),
        "Reputation": random.randint(60, 90),
        "Activity": random.randint(70, 95)
    }

def get_mock_resume_score() -> Dict[str, Any]:
    """
    Generate mock resume analysis with scores and insights.
    
    Returns:
        Dict with scores, summary, and keywords
    """
    # Generate different mock data based on the skills
    skills = [
        "Python", "JavaScript", "TypeScript", "React", "Node.js", 
        "SQL", "AWS", "Docker", "Kubernetes", "TensorFlow", 
        "PyTorch", "Java", "C++", "Go", "Ruby", "Swift"
    ]
    
    # Select 3-5 random skills
    selected_skills = random.sample(skills, random.randint(3, 5))
    
    # Generate a brief summary
    experience_years = random.randint(2, 8)
    summary = f"Experienced developer with {experience_years} years in {', '.join(selected_skills[:2])}"
    
    return {
        "Technical_Skills": random.randint(70, 90),
        "Reputation": random.randint(65, 85),
        "Activity": random.randint(70, 90),
        "summary": summary,
        "keywords": selected_skills
    } 