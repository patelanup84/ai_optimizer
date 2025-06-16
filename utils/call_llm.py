# utils/call_llm.py
# utils/call_llm.py
from openai import OpenAI
import os

def call_llm(prompt, model="gpt-4o-mini"):
    """Call OpenAI LLM with the given prompt"""
    try:
        # Corrected this line: Use OpenAI directly, not openai.OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Ensure the API key was found
        if not client.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM call failed: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    test_prompt = "What is brand monitoring?. Limit your response to 20 words or less"
    print(call_llm(test_prompt))
