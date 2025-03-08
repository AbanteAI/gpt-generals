import json
import os
from typing import Dict, List, Optional, Type, TypeVar, Union

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel


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

    # If a response model is provided, use structured output
    if response_model:
        # Extract Pydantic schema for the function call
        schema = response_model.model_json_schema()

        function_name = response_model.__name__
        functions = [
            {
                "type": "function",
                "function": {
                    "name": function_name,
                    "description": f"Output structured as {function_name}",
                    "parameters": schema,
                },
            }
        ]

        # Make the API call with the function definition
        completion = client.chat.completions.create(
            extra_headers=extra_headers,
            model=model,
            messages=openai_messages,
            functions=functions,
            function_call={"name": function_name},
        )

        # Extract and parse the function call arguments
        function_call = completion.choices[0].message.function_call
        if not function_call or not function_call.arguments:
            raise ValueError("No function call arguments in response")

        # Parse the JSON arguments and convert to the Pydantic model
        try:
            args_dict = json.loads(function_call.arguments)
            return response_model.model_validate(args_dict)
        except Exception as e:
            raise ValueError(f"Failed to parse structured output: {e}") from e
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
