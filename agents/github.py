import openai
import os
import json
import re
from typing import Dict, Any
from utils.logging.logger import log
from utils.mock_data import get_mock_github_score

# Load environment variables and configuration
openai_api_key = os.getenv("OPENAI_API_KEY")
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
use_mock = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

def analyze_github(github_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process GitHub data to extract scores for technical skills, reputation, and activity.
    Uses OpenRouter/Deepseek API with OpenAI as fallback.
    Falls back to mock data if APIs fail or if USE_MOCK_DATA=true.
    
    This function can work in two modes:
    1. If github_data already contains the required score fields, it uses them directly.
    2. If raw GitHub API data is provided, it uses LLM to analyze it.
    
    Args:
        github_data: Dictionary with either score fields or raw GitHub API data
        
    Returns:
        Dictionary with normalized scores
    """
    # Check if the data already contains the required score fields
    required_fields = ["Technical_Skills", "Reputation", "Activity"]
    if all(field in github_data for field in required_fields):
        # Data already contains the required fields, validate and normalize
        result = {
            "Technical_Skills": github_data["Technical_Skills"],
            "Reputation": github_data["Reputation"],
            "Activity": github_data["Activity"]
        }
        
        # Ensure scores are within range
        for field in required_fields:
            if not isinstance(result[field], (int, float)):
                log.warning(f"GitHub {field} score is not a number, defaulting to 50")
                result[field] = 50
            result[field] = max(0, min(100, int(result[field])))
            
        return result
    
    # If mock mode is enabled, return mock data immediately
    if use_mock:
        log.info("Using mock data for GitHub analysis (USE_MOCK_DATA=true)")
        return get_mock_github_score()
        
    try:
        # If data doesn't contain required fields, assume it's raw GitHub data
        # and use LLM to analyze it
        prompt = f"""
        Analyze this GitHub data and give scores (0-100) for:
        - Technical_Skills: Based on languages used, repositories, code quality indicators
        - Reputation: Based on stars, followers, contributions to other projects
        - Activity: Based on frequency of commits, consistency, recency
        
        Return only a JSON object with the scores as integers.
        
        GitHub Data:
        ```
        {json.dumps(github_data, indent=2)}
        ```
        
        Respond only with valid JSON in this format:
        {{
          "Technical_Skills": 75,
          "Reputation": 80,
          "Activity": 65
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
                log.info("Attempting to analyze GitHub data with OpenRouter/Deepseek API")
                openrouter_client = openai.OpenAI(
                    api_key=openrouter_api_key,
                    base_url="https://openrouter.ai/api/v1"
                )
                
                response = openrouter_client.chat.completions.create(
                    model="deepseek/deepseek-chat-v3-0324",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that analyzes GitHub profiles and returns structured JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    extra_headers={
                        "HTTP-Referer": "https://trustz.ai",
                        "X-Title": "TrustZ AI GitHub Analyzer"
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
                log.info("Attempting to analyze GitHub data with Deepseek API directly")
                deepseek_client = openai.OpenAI(
                    api_key=deepseek_api_key,
                    base_url="https://api.deepseek.com"
                )
                
                response = deepseek_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that analyzes GitHub profiles and returns structured JSON."},
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
                log.info("Attempting to analyze GitHub data with OpenAI API")
                openai_client = openai.OpenAI(
                    api_key=openai_api_key
                )
                
                response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that analyzes GitHub profiles and returns structured JSON."},
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
            log.error("No API keys were available for GitHub analysis")
            
        # Return mock data as a fallback
        log.info("Using mock data as fallback for GitHub analysis")
        return get_mock_github_score()
    
    except Exception as e:
        log.error(f"Unexpected error analyzing GitHub data: {str(e)}")
        # Return mock data for any other errors
        log.info("Using mock data due to unexpected error in GitHub analysis")
        return get_mock_github_score()

def process_llm_response(result_text: str) -> Dict[str, Any]:
    """
    Process and validate the response from an LLM.
    
    Args:
        result_text: Raw text response from LLM
        
    Returns:
        Processed and validated dictionary
    """
    try:
        # Required fields for a valid response
        required_fields = ["Technical_Skills", "Reputation", "Activity"]
        
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
        for field in required_fields:
            if field not in result:
                log.warning(f"GitHub analysis missing {field} score, defaulting to 50")
                result[field] = 50
        
        # Ensure scores are within range
        for field in required_fields:
            if isinstance(result[field], str):
                try:
                    result[field] = int(result[field])
                except ValueError:
                    result[field] = 50
            result[field] = max(0, min(100, int(result[field])))
            
        return result
        
    except Exception as e:
        log.error(f"Error processing LLM response: {str(e)}")
        # Return mock data as a fallback for processing errors
        return get_mock_github_score()

def extract_values_from_text(text: str) -> Dict[str, Any]:
    """
    Extract values from text when JSON parsing fails
    """
    result = {
        "Technical_Skills": 50,
        "Reputation": 50,
        "Activity": 50
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
    
    return result
