# utils/ai_platforms.py
import os
import time
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def query_chatgpt(query: str) -> Dict[str, Any]:
    """Query ChatGPT and return response with metadata"""
    try:
        try:
            try:
                from utils.call_llm import call_llm
            except ImportError:
                from call_llm import call_llm
        except ImportError:
            from call_llm import call_llm
        
        prompt = f"Please answer this question as you would for any user: {query}"
        response = call_llm(prompt)
        
        return {
            "platform": "chatgpt",
            "query": query,
            "response": response,
            "timestamp": time.time(),
            "status": "success"
        }
    except Exception as e:
        return {
            "platform": "chatgpt", 
            "query": query,
            "response": "",
            "timestamp": time.time(),
            "status": "error",
            "error": str(e)
        }

def query_gemini(query: str) -> Dict[str, Any]:
    """Query Google Gemini and return response with metadata"""
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise Exception("GOOGLE_API_KEY not found in environment variables")
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')  # Updated model name
        response = model.generate_content(query)
        
        return {
            "platform": "gemini",
            "query": query, 
            "response": response.text,
            "timestamp": time.time(),
            "status": "success"
        }
    except Exception as e:
        # Fallback to OpenAI simulation
        print(f"Gemini API failed, using OpenAI fallback: {e}")
        try:
            from utils.call_llm import call_llm
            prompt = f"[Simulating Gemini response] {query}"
            response = call_llm(prompt)
            
            return {
                "platform": "gemini",
                "query": query,
                "response": f"[Simulated] {response}",
                "timestamp": time.time(),
                "status": "fallback"
            }
        except Exception as e2:
            return {
                "platform": "gemini",
                "query": query,
                "response": "",
                "timestamp": time.time(),
                "status": "error", 
                "error": str(e2)
            }

if __name__ == "__main__":
    print("=== Environment Check ===")
    print(f"OPENAI_API_KEY: {'✓ Found' if os.getenv('OPENAI_API_KEY') else '✗ Missing'}")
    print(f"GOOGLE_API_KEY: {'✓ Found' if os.getenv('GOOGLE_API_KEY') else '✗ Missing'}")
    print()
    
    test_query = "What do you know about Tesla cars?"
    
    print("=== Testing ChatGPT ===")
    result1 = query_chatgpt(test_query)
    print(f"Status: {result1['status']}")
    if result1['status'] == 'error':
        print(f"Error: {result1.get('error')}")
    else:
        print(f"Response: {result1['response'][:100]}...")
    
    print("\n=== Testing Gemini ===")
    result2 = query_gemini(test_query)
    print(f"Status: {result2['status']}")
    if result2['status'] == 'error':
        print(f"Error: {result2.get('error')}")
    else:
        print(f"Response: {result2['response'][:100]}...")