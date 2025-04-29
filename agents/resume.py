import openai
import os
import json
import re
from typing import Dict, Any, List
from utils.logging.logger import log
from utils.mock_data import get_mock_resume_score

# Load environment variables and configuration
openai_api_key = os.getenv("OPENAI_API_KEY")
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
use_mock = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

def analyze_resume(resume_text: str) -> Dict[str, Any]:
    """
    Analyze a resume using OpenRouter/Deepseek API to extract scores and insights.
    Falls back to OpenAI, then to mock data if APIs fail or if USE_MOCK_DATA=true.
    
    Args:
        resume_text: The text content of the resume
        
    Returns:
        Dictionary with scores for technical skills, reputation, activity,
        plus a summary and extracted keywords
    """
    # If mock mode is enabled, return mock data immediately
    if use_mock:
        log.info("Using mock data for resume analysis (USE_MOCK_DATA=true)")
        return get_mock_resume_score()
    
    try:
        if not resume_text:
            log.warning("Empty resume text provided for analysis")
            return {
                "Technical_Skills": 50,
                "Reputation": 50,
                "Activity": 50,
                "summary": "No resume provided for analysis",
                "keywords": []
            }
        
        # Prepare the prompt for LLM analysis
        prompt = f"""
        Analyze the following resume and return a JSON object with:
        
        1. Scores (0-100) for:
           - Technical_Skills: Based on technical knowledge and experiences
           - Reputation: Based on achievements, education, certifications
           - Activity: Based on career progression, frequency of roles, projects
           
        2. A concise one-sentence summary (max 100 chars)
        
        3. A list of up to 5 main keywords/skills extracted from the resume
        
        Make sure to escape any special characters in the JSON.
        
        Resume:
        ```
        {resume_text}
        ```
        
        Respond only with valid JSON in this format:
        {{
          "Technical_Skills": 75,
          "Reputation": 80,
          "Activity": 65,
          "summary": "Brief summary...",
          "keywords": ["keyword1", "keyword2", "keyword3"]
        }}
        """
        
        # Track whether we've tried each API
        tried_openrouter = False
        tried_deepseek = False
        tried_openai = False
        
        # Try OpenRouter first if key is available (to access Deepseek model)
        if openrouter_api_key:
            try:
                tried_openrouter = True
                log.info("Attempting to analyze resume with OpenRouter/Deepseek API")
                openrouter_client = openai.OpenAI(
                    api_key=openrouter_api_key,
                    base_url="https://openrouter.ai/api/v1"
                )
                
                response = openrouter_client.chat.completions.create(
                    model="deepseek/deepseek-chat-v3-0324",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that analyzes resumes and returns structured JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    extra_headers={
                        "HTTP-Referer": "https://trustz.ai",
                        "X-Title": "TrustZ AI Resume Analyzer"
                    }
                )
                result_text = response.choices[0].message.content.strip()
                log.info("Successfully received response from OpenRouter/Deepseek API")
                
                # If we get here, processing was successful
                return process_llm_response(result_text)
                
            except Exception as openrouter_error:
                log.warning(f"OpenRouter API failed: {str(openrouter_error)}")
                # Continue to try other options
        else:
            log.warning("No OpenRouter API key available, skipping OpenRouter")
        
        # Try Deepseek directly if key is available
        if deepseek_api_key:
            try:
                tried_deepseek = True
                log.info("Attempting to analyze resume with Deepseek API directly")
                deepseek_client = openai.OpenAI(
                    api_key=deepseek_api_key,
                    base_url="https://api.deepseek.com"
                )
                
                response = deepseek_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that analyzes resumes and returns structured JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                )
                result_text = response.choices[0].message.content.strip()
                log.info("Successfully received response from Deepseek API")
                
                # If we get here, processing was successful
                return process_llm_response(result_text)
                
            except Exception as deepseek_error:
                log.warning(f"Deepseek API failed: {str(deepseek_error)}")
                # Continue to try OpenAI
        else:
            log.warning("No Deepseek API key available, skipping Deepseek API")
                
        # Try OpenAI API if key is available and other options failed
        if openai_api_key:
            try:
                tried_openai = True
                log.info("Attempting to analyze resume with OpenAI API")
                openai_client = openai.OpenAI(
                    api_key=openai_api_key
                )
                
                response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that analyzes resumes and returns structured JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5,
                    response_format={"type": "json_object"}
                )
                result_text = response.choices[0].message.content.strip()
                log.info("Successfully received response from OpenAI API")
                
                # If we get here, processing was successful
                return process_llm_response(result_text)
                
            except Exception as openai_error:
                log.warning(f"OpenAI API failed: {str(openai_error)}")
                # Fall through to the fallback
        else:
            log.warning("No OpenAI API key available, skipping OpenAI API")
            
        # If we've tried APIs and all failed, or if no APIs were available
        apis_tried = []
        if tried_openrouter:
            apis_tried.append("OpenRouter/Deepseek")
        if tried_deepseek:
            apis_tried.append("Deepseek")
        if tried_openai:
            apis_tried.append("OpenAI")
            
        if apis_tried:
            log.error(f"All available APIs failed: {', '.join(apis_tried)}")
        else:
            log.error("No API keys were available for resume analysis")
            
        # Return mock data as a fallback
        log.info("Using mock data as fallback for resume analysis")
        return get_mock_resume_score()
    
    except Exception as e:
        log.error(f"Unexpected error analyzing resume: {str(e)}")
        # Return mock data for any other errors
        log.info("Using mock data due to unexpected error in resume analysis")
        return get_mock_resume_score()
        
def process_llm_response(result_text: str) -> Dict[str, Any]:
    """
    Process and validate the response from an LLM.
    
    Args:
        result_text: Raw text response from LLM
        
    Returns:
        Processed and validated dictionary
    """
    try:
        # Try to parse JSON result
        try:
            # Parse the response - handle case where response might not be valid JSON
            # First, try to find JSON within the response if it's not pure JSON
            json_pattern = r'(\{.*\})'
            json_match = re.search(json_pattern, result_text, re.DOTALL)
            
            if json_match:
                result_text = json_match.group(1)
                
            result = json.loads(result_text)
            log.info("Successfully parsed JSON response")
            
        except json.JSONDecodeError:
            log.warning(f"Could not parse JSON from response: {result_text[:100]}...")
            # Attempt a more forgiving parse by extracting values with regex
            result = extract_values_from_text(result_text)
        
        # Ensure all required fields are present
        required_fields = ["Technical_Skills", "Reputation", "Activity", "summary", "keywords"]
        for field in required_fields:
            if field not in result:
                if field in ["Technical_Skills", "Reputation", "Activity"]:
                    result[field] = 50
                elif field == "summary":
                    result[field] = "Resume analysis incomplete"
                elif field == "keywords":
                    result[field] = []
        
        # Ensure scores are within range
        for score_field in ["Technical_Skills", "Reputation", "Activity"]:
            if isinstance(result[score_field], str):
                try:
                    result[score_field] = int(result[score_field])
                except ValueError:
                    result[score_field] = 50
            result[score_field] = max(0, min(100, result[score_field]))
            
        return result
        
    except Exception as e:
        log.error(f"Error processing LLM response: {str(e)}")
        # Return mock data as a fallback for processing errors
        return get_mock_resume_score()

def extract_values_from_text(text: str) -> Dict[str, Any]:
    """
    Extract values from text when JSON parsing fails
    """
    import re
    
    result = {
        "Technical_Skills": 50,
        "Reputation": 50,
        "Activity": 50,
        "summary": "Extracted from non-JSON response",
        "keywords": []
    }
    
    # Try to extract scores
    technical_match = re.search(r'Technical_?Skills["\s:]+(\d+)', text)
    if technical_match:
        result["Technical_Skills"] = int(technical_match.group(1))
        
    reputation_match = re.search(r'Reputation["\s:]+(\d+)', text)
    if reputation_match:
        result["Reputation"] = int(reputation_match.group(1))
        
    activity_match = re.search(r'Activity["\s:]+(\d+)', text)
    if activity_match:
        result["Activity"] = int(activity_match.group(1))
    
    # Try to extract summary
    summary_match = re.search(r'summary["\s:]+["\']([^"\']+)["\']', text)
    if summary_match:
        result["summary"] = summary_match.group(1)
    
    # Try to extract keywords
    keywords_match = re.search(r'keywords["\s:]+\[(.*?)\]', text, re.DOTALL)
    if keywords_match:
        keywords_text = keywords_match.group(1)
        keywords = re.findall(r'["\']([^"\']+)["\']', keywords_text)
        result["keywords"] = keywords
    
    return result
