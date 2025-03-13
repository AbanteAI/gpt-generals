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

    parsed: Optional[T]
    raw: str
    refusal: Optional[str] = None


def call_openrouter(
    messages: Messages,
    model: str = "openai/gpt-4o-mini",
) -> str:
    """
    Make an API call to OpenRouter for standard text completion.

    Args:
        messages: Instance of Messages class with conversation history
        model: Model to use (defaults to gpt-4o-mini)

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

    openai_messages = messages.to_openai_messages()

    # Standard non-structured response
    completion = client.chat.completions.create(model=model, messages=openai_messages)

    content = completion.choices[0].message.content
    if content is None:
        raise ValueError("No content in response")
    return content


def call_openrouter_structured(
    messages: Messages,
    response_model: Type[T],
    model: str = "openai/gpt-4o-mini",
) -> ParsedResponse[T]:
    """
    Make an API call to OpenRouter with structured output parsing.

    Args:
        messages: Instance of Messages class with conversation history
        response_model: Pydantic model for structured output parsing
        model: Model to use (defaults to gpt-4o-mini)

    Returns:
        A ParsedResponse object containing parsed model, raw string, and any refusal message

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

    openai_messages = messages.to_openai_messages()

    # Use the parsing API - will raise exceptions if not available
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=openai_messages,
        response_format=response_model,
    )

    message = completion.choices[0].message
    raw_response = message.content

    if raw_response is None:
        raise ValueError("No content in response")

    # Check if the model refused to respond
    refusal = getattr(message, "refusal", None)
    if refusal:
        return ParsedResponse(parsed=None, raw=raw_response, refusal=refusal)

    # If no refusal, return the parsed response
    parsed_response = cast(T, message.parsed)
    return ParsedResponse(parsed=parsed_response, raw=raw_response)


def handle_structured_response_with_refusal(parsed_response: ParsedResponse[T]) -> None:
    """
    Example of how to handle a structured response that might contain a refusal.

    Args:
        parsed_response: A ParsedResponse object that might contain a refusal
    """
    if parsed_response.refusal:
        print("Model refused to respond:")
        print(parsed_response.refusal)
    else:
        print("Successfully parsed response:")
        print(parsed_response.parsed)

    # Raw response is always available
    print("\nRaw response:")
    print(parsed_response.raw)


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

    # The following is an example of how you could use the structured output with refusal handling
    # Uncomment and modify to test with an actual Pydantic model
    """
    from pydantic import BaseModel

    class ExampleOutput(BaseModel):
        answer: str
        confidence: float

    structured_messages = Messages()
    structured_messages.add_system_message(
        "You are a helpful assistant that provides structured outputs."
    )
    structured_messages.add_user_message("What is 2+2?")

    try:
        result = call_openrouter_structured(structured_messages, ExampleOutput)
        handle_structured_response_with_refusal(result)
    except Exception as e:
        print("Structured test failed:", str(e))
    """
