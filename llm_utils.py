import os
from dataclasses import dataclass
from typing import Dict, Generic, List, Optional, Type, TypeVar, cast

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
) -> str:
    """
    Make an API call to OpenRouter for standard text completion.

    Args:
        messages: Instance of Messages class with conversation history
        model: Model to use (defaults to gpt-4o-mini)
        site_url: Optional site URL for OpenRouter rankings
        site_name: Optional site name for OpenRouter rankings

    Returns:
        A string response from the model

    Raises:
        ValueError: If OPEN_ROUTER_KEY environment variable is not set or if response has no content
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

    # Standard non-structured response
    completion = client.chat.completions.create(
        extra_headers=extra_headers, model=model, messages=openai_messages
    )

    content = completion.choices[0].message.content
    if content is None:
        raise ValueError("No content in response")
    return content


def call_openrouter_structured(
    messages: Messages,
    response_model: Type[T],
    model: str = "openai/gpt-4o-mini",
    site_url: Optional[str] = None,
    site_name: Optional[str] = None,
) -> ParsedResponse[T]:
    """
    Make an API call to OpenRouter with structured output parsing.

    Args:
        messages: Instance of Messages class with conversation history
        response_model: Pydantic model for structured output parsing
        model: Model to use (defaults to gpt-4o-mini)
        site_url: Optional site URL for OpenRouter rankings
        site_name: Optional site name for OpenRouter rankings

    Returns:
        A ParsedResponse object containing both parsed model and raw string

    Raises:
        ValueError: If OPEN_ROUTER_KEY environment variable is not set or if response has no content
        Exception: If parsing fails or API call fails
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

    try:
        # Try to use the parsing API - will raise exceptions if not available
        completion = client.beta.chat.completions.parse(
            extra_headers=extra_headers,
            model=model,
            messages=openai_messages,
            response_format=response_model,
        )

        # Get both parsed model and raw content
        # Check if choices and message exist before accessing
        if not completion.choices:
            raise ValueError("No choices in API response")

        # Safely access the parsed response
        message = completion.choices[0].message
        if not hasattr(message, "parsed") or message.parsed is None:
            raise ValueError("No parsed data in API response")

        parsed_response = cast(T, message.parsed)

        # The raw content might be None, which is okay - we'll handle it later
        raw_response = message.content

        # Return both in a ParsedResponse object
        return ParsedResponse(parsed=parsed_response, raw=raw_response or "")

    except Exception as e:
        # If parsing fails, fall back to standard completion and handle the response manually
        print(f"Structured parsing failed: {e}. Falling back to standard completion.")

        try:
            # Standard non-structured response
            completion = client.chat.completions.create(
                extra_headers=extra_headers, model=model, messages=openai_messages
            )

            raw_content = completion.choices[0].message.content
            if raw_content is None:
                raise ValueError("No content in fallback response")

            # Try to parse the raw content manually into our model
            try:
                import json

                from pydantic import ValidationError

                # Try to extract JSON from the text response
                # Look for content between ```json and ``` or just parse the whole thing
                json_content = raw_content
                if "```json" in raw_content and "```" in raw_content.split("```json")[1]:
                    json_part = raw_content.split("```json")[1].split("```")[0].strip()
                    json_content = json_part

                # Parse as JSON and create model
                data = json.loads(json_content)
                parsed_model = response_model.parse_obj(data)

                return ParsedResponse(parsed=parsed_model, raw=raw_content)

            except (json.JSONDecodeError, ValidationError) as json_err:
                # If manual parsing fails, raise a detailed error
                raise ValueError(
                    f"Failed to parse response as {response_model.__name__}: {json_err}. Response: {raw_content}"
                )

        except Exception as fallback_err:
            # If both methods fail, raise with details
            raise Exception(f"Both structured and fallback parsing failed: {fallback_err}")


if __name__ == "__main__":
    # Test the standard function using the Messages class
    test_messages = Messages()
    test_messages.add_user_message("What is the meaning of life?")

    try:
        response = call_openrouter(test_messages)
        print("Test successful!")
        print("Response:", response)
    except Exception as e:
        print("Test failed:", str(e))
