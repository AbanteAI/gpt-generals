import os
from typing import Dict, List, Optional, Type, TypeVar, Union

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()


class Messages:
    """A simple class to manage messages for LLM conversations."""

    def __init__(self):
        """Initialize an empty message list."""
        self.messages: List[Dict[str, str]] = []

    def add_user_message(self, content: str) -> None:
        """Add a user message to the list."""
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the list."""
        self.messages.append({"role": "assistant", "content": content})

    def add_system_message(self, content: str) -> None:
        """Add a system message to the list."""
        self.messages.append({"role": "system", "content": content})

    def to_openai_messages(self) -> List[ChatCompletionMessageParam]:
        """Convert the messages to the format required by the OpenAI API."""
        return self.messages  # type: ignore


T = TypeVar("T", bound=BaseModel)


def call_openrouter(
    messages: Messages,
    model: str = "openai/gpt-4o-mini",
    site_url: Optional[str] = None,
    site_name: Optional[str] = None,
    response_model: Optional[Type[T]] = None,
) -> Union[str, T]:
    """
    Make an API call to OpenRouter, optionally with structured output.

    Args:
        messages: Instance of Messages class with conversation history
        model: Model to use (defaults to gpt-4o-mini)
        site_url: Optional site URL for OpenRouter rankings
        site_name: Optional site name for OpenRouter rankings
        response_model: Optional Pydantic model for structured output

    Returns:
        Either a string response or a Pydantic model instance if response_model is provided

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

    openai_messages = messages.to_openai_messages()

    # Common parameters for API calls
    params = {
        "extra_headers": extra_headers,
        "model": model,
        "messages": openai_messages,
    }

    # Add response_format parameter if a model is provided
    if response_model:
        params["response_format"] = {"type": "json_object"}

    try:
        # Always use the standard create method
        print(f"Calling OpenRouter API with params: {str(params)}")
        completion = client.chat.completions.create(**params)
        
        print(f"Response received. Type: {type(completion)}")
        
        # Check if we have valid response data
        if not completion:
            print("Error: Completion object is None")
            raise ValueError("Invalid response structure from OpenRouter - completion is None")
            
        if not hasattr(completion, 'choices') or not completion.choices:
            print(f"Error: No choices in completion. Response: {str(completion)}")
            raise ValueError("Invalid response - no choices in completion")
            
        if len(completion.choices) == 0:
            print(f"Error: Empty choices list in response: {str(completion)}")
            raise ValueError("Invalid response - empty choices list")
            
        print(f"Completion has {len(completion.choices)} choices")
        choice = completion.choices[0]
        if not choice:
            print("Error: First choice is None")
            raise ValueError("Invalid choice object in response")
            
        message = choice.message
        if message is None:
            print(f"Error: No message in choice: {str(choice)}")
            raise ValueError("No message in response")
            
        print(f"Message: {str(message)}")
        content = message.content
        if content is None:
            print("Error: No content in message")
            raise ValueError("No content in response message")
            
        print(f"Content received (first 100 chars): {content[:100]}...")

        # If a response model was provided, parse the content into the model
        if response_model:
            print(f"Parsing with model: {response_model.__name__}")
            try:
                result = response_model.model_validate_json(content)
                print(f"Successfully parsed into {response_model.__name__} object")
                return result
            except Exception as parse_error:
                print(f"Error parsing JSON content: {str(parse_error)}")
                print(f"Content that failed to parse: {content}")
                raise ValueError(f"Failed to parse content as {response_model.__name__}: {str(parse_error)}")
        else:
            return content
            
    except Exception as e:
        # Add better error handling and debugging
        error_msg = f"OpenRouter API error: {str(e)}"
        print(f"Error details: {error_msg}")
        if "OPEN_ROUTER_KEY" in str(e):
            print("Check that your OPEN_ROUTER_KEY environment variable is set correctly")
        raise ValueError(error_msg) from e


if __name__ == "__main__":
    # Test the function using the new Messages class
    test_messages = Messages()
    test_messages.add_user_message("What is the meaning of life?")

    try:
        response = call_openrouter(test_messages)
        print("Test successful!")
        print("Response:", response)
    except Exception as e:
        print("Test failed:", str(e))
