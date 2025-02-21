from typing import Dict, List, Optional

import os
from openai import OpenAI

def call_openrouter(
    messages: List[Dict[str, str]],
    model: str = "openai/gpt-4o-mini",
    site_url: Optional[str] = None,
    site_name: Optional[str] = None,
) -> str:
    """
    Make an API call to OpenRouter.

    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: Model to use (defaults to gpt-4o-mini)
        site_url: Optional site URL for OpenRouter rankings
        site_name: Optional site name for OpenRouter rankings

    Returns:
        The response content from the model

    Raises:
        ValueError: If OPEN_ROUTER_KEY environment variable is not set
    """
    api_key = os.getenv("OPEN_ROUTER_KEY")
    if not api_key:
        raise ValueError("OPEN_ROUTER_KEY environment variable must be set")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    extra_headers = {}
    if site_url:
        extra_headers["HTTP-Referer"] = site_url
    if site_name:
        extra_headers["X-Title"] = site_name

    completion = client.chat.completions.create(
        extra_headers=extra_headers,
        model=model,
        messages=messages
    )

    return completion.choices[0].message.content

if __name__ == "__main__":
    # Test the function
    test_messages = [
        {
            "role": "user",
            "content": "What is the meaning of life?"
        }
    ]

    try:
        response = call_openrouter(test_messages)
        print("Test successful!")
        print("Response:", response)
    except Exception as e:
        print("Test failed:", str(e))
