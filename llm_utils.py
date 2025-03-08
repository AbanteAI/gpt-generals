import os
from typing import Dict, List, Optional

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam


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


def call_openrouter(
    messages: Messages,
    model: str = "openai/gpt-4o-mini",
    site_url: Optional[str] = None,
    site_name: Optional[str] = None,
) -> str:
    """
    Make an API call to OpenRouter.

    Args:
        messages: Instance of Messages class with conversation history
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

    openai_messages = messages.to_openai_messages()

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
