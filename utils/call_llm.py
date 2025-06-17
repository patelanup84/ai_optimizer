# utils/call_llm.py
from openai import OpenAI
import os
import logging
from functools import lru_cache
from typing import Union, List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def call_llm(prompt: Union[str, List[Dict[str, str]]], 
             model: str = "gpt-4o-mini",
             temperature: float = 0.7,
             max_tokens: int = None,
             use_cache: bool = True) -> str:
    """
    Enhanced LLM wrapper following PocketFlow best practices
    
    Args:
        prompt: String prompt or list of message dicts
        model: OpenAI model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        use_cache: Whether to use cached results (disable for retries)
    
    Returns:
        LLM response as string
    """
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        if not client.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        # Prepare messages
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = prompt

        # Prepare request parameters
        request_params = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            request_params["max_tokens"] = max_tokens

        # Log the request (without sensitive data)
        logger.info(f"LLM Request - Model: {model}, Messages: {len(messages)}")
        
        response = client.chat.completions.create(**request_params)
        
        result = response.choices[0].message.content
        
        # Log response length
        logger.info(f"LLM Response - Length: {len(result)} chars")
        
        return result
        
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise e

@lru_cache(maxsize=1000)
def cached_call_llm(prompt: str, model: str = "gpt-4o-mini") -> str:
    """Cached version for performance optimization"""
    return call_llm(prompt, model, use_cache=False)

def call_llm_structured(prompt: str, 
                       output_format: str = "yaml",
                       model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Call LLM with structured output parsing
    
    Args:
        prompt: The prompt to send
        output_format: Expected output format ("yaml" or "json")
        model: OpenAI model to use
    
    Returns:
        Parsed structured output as dict
    """
    import yaml
    import json
    
    # Add format instructions to prompt
    if output_format == "yaml":
        format_prompt = f"""
{prompt}

Output your response in YAML format within code fences:
```yaml
# Your structured response here
```
"""
    elif output_format == "json":
        format_prompt = f"""
{prompt}

Output your response in JSON format within code fences:
```json
{{
  // Your structured response here
}}
```
"""
    else:
        raise ValueError(f"Unsupported output format: {output_format}")
    
    response = call_llm(format_prompt, model)
    
    try:
        # Extract content between code fences
        if output_format == "yaml":
            yaml_str = response.split("```yaml")[1].split("```")[0].strip()
            return yaml.safe_load(yaml_str)
        elif output_format == "json":
            json_str = response.split("```json")[1].split("```")[0].strip()
            return json.loads(json_str)
    except Exception as e:
        logger.error(f"Failed to parse structured output: {e}")
        logger.error(f"Raw response: {response}")
        raise ValueError(f"Failed to parse {output_format} output: {e}")

def call_llm_with_retry(prompt: str, 
                       max_retries: int = 3, 
                       wait_time: int = 1,
                       model: str = "gpt-4o-mini") -> str:
    """
    Call LLM with automatic retry logic
    
    Args:
        prompt: The prompt to send
        max_retries: Maximum number of retries
        wait_time: Seconds to wait between retries
        model: OpenAI model to use
    
    Returns:
        LLM response as string
    """
    import time
    
    for attempt in range(max_retries):
        try:
            return call_llm(prompt, model)
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Final retry failed after {max_retries} attempts: {e}")
                raise e
            
            logger.warning(f"LLM call failed (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(wait_time)
    
    raise Exception("Unexpected retry loop exit")

if __name__ == "__main__":
    # Test basic functionality
    test_prompt = "What is brand monitoring? Limit your response to 20 words or less"
    print("Basic test:", call_llm(test_prompt))
    
    # Test structured output
    structured_prompt = """
    Generate a simple brand analysis with these fields:
    - brand_name: string
    - sentiment: positive/negative/neutral
    - confidence: 0-100
    """
    try:
        result = call_llm_structured(structured_prompt, "yaml")
        print("Structured test:", result)
    except Exception as e:
        print(f"Structured test failed: {e}")
