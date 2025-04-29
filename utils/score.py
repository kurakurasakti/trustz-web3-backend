from typing import Dict, Any
from utils.logging.logger import log

def calculate_trust_score(github_score: Dict[str, Any], resume_score: Dict[str, Any]) -> int:
    """
    Calculate the overall trust score based on GitHub and resume analysis.
    
    Args:
        github_score: Dictionary containing GitHub analysis scores
        resume_score: Dictionary containing resume analysis scores
        
    Returns:
        Integer trust score from 0-100
    """
    try:
        # Extract technical, reputation, and activity scores from both sources
        github_technical = github_score.get("Technical_Skills", 0)
        github_reputation = github_score.get("Reputation", 0)
        github_activity = github_score.get("Activity", 0)
        
        resume_technical = resume_score.get("Technical_Skills", 0)
        resume_reputation = resume_score.get("Reputation", 0)
        resume_activity = resume_score.get("Activity", 0)
        
        # Calculate weighted average (can be adjusted based on importance)
        # Currently weighing GitHub scores slightly higher (60%) than resume scores (40%)
        final_score = round(
            (github_technical * 0.25 +
             github_reputation * 0.15 +
             github_activity * 0.2 +
             resume_technical * 0.2 +
             resume_reputation * 0.1 +
             resume_activity * 0.1),
            0
        )
        
        # Ensure score is within range
        return max(0, min(100, int(final_score)))
    except Exception as e:
        log.error(f"Error calculating trust score: {str(e)}")
        # Return a default score if calculation fails
        return 50
