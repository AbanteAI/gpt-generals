import os
from dataclasses import dataclass
from typing import Dict, Generic, List, Optional, Type, TypeVar, Union, cast

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


@dataclass
class ParsedResponse(Generic[T]):
    """Class to hold both parsed and raw responses from LLM."""

    parsed: T
    raw: str


def call_openrouter(
    messages: Messages,
    model: str = "openai/gpt-4o-mini",
    site_url: Optional[str] = None,
    site_name: Optional[str] = None,
    response_model: Optional[Type[T]] = None,
) -> Union[str, "ParsedResponse[T]"]:  # Forward reference for type checking
    """
    Make an API call to OpenRouter, optionally with structured output.

    Args:
        messages: Instance of Messages class with conversation history
        model: Model to use (defaults to gpt-4o-mini)
        site_url: Optional site URL for OpenRouter rankings
        site_name: Optional site name for OpenRouter rankings
        response_model: Optional Pydantic model for structured output

    Returns:
        Either:
        - A string response when response_model is None
        - A ParsedResponse object containing both parsed model and raw string
          when response_model is provided

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

    # If a response model is provided, use structured output
    if response_model:
        # Use the parsing API - will raise exceptions if not available
        completion = client.beta.chat.completions.parse(
            extra_headers=extra_headers,
            model=model,
            messages=openai_messages,
            response_format=response_model,
        )

        # Get both parsed model and raw content
        parsed_response = cast(T, completion.choices[0].message.parsed)
        raw_response = completion.choices[0].message.content

        if raw_response is None:
            raise ValueError("No content in response")

        # Return both in a ParsedResponse object
        return ParsedResponse(parsed=parsed_response, raw=raw_response)
    else:
        # Standard non-structured response
        completion = client.chat.completions.create(
            extra_headers=extra_headers, model=model, messages=openai_messages
        )

        content = completion.choices[0].message.content
        if content is None:
            raise ValueError("No content in response")
        return content


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
