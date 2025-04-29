import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables for local testing
load_dotenv()

# API endpoint
API_URL = "http://localhost:8000/analyze"

# Test data
test_data = {
    "github": {
        "Technical_Skills": 85,
        "Reputation": 72,
        "Activity": 90
    },
    "resume": """
    John Doe
    Senior Software Engineer

    Skills:
    - Python, JavaScript, TypeScript, React
    - AWS, Docker, Kubernetes
    - Machine Learning, Data Analysis

    Experience:
    - Senior Software Engineer, Tech Co (2020-Present)
      Led development of microservices architecture, reducing system latency by 40%
    
    - Software Developer, StartupXYZ (2018-2020)
      Developed front-end components using React and TypeScript
    
    Education:
    - M.S. Computer Science, University of Technology (2018)
    - B.S. Computer Engineering, State University (2016)
    """
}

def test_analyze_endpoint():
    """Test the /analyze endpoint with sample data"""
    try:
        # Send request
        response = requests.post(API_URL, json=test_data)
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        
        # Print formatted result
        print("API Test Results:")
        print("-" * 50)
        print(f"Trust Score: {result['trust_score']}")
        print("\nResume Analysis:")
        print(f"  Summary: {result['resume_analysis']['summary']}")
        print("  Keywords:", ", ".join(result['resume_analysis']['keywords']))
        
        print("\nGitHub Scores:")
        for key, value in result['github_score'].items():
            print(f"  {key}: {value}")
        
        print("\nResume Scores:")
        for key, value in result['resume_score'].items():
            if key not in ['summary', 'keywords']:
                print(f"  {key}: {value}")
        
        print("-" * 50)
        print("Test completed successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to API: {e}")
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    test_analyze_endpoint() 