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

    # Add response_format parameter and schema details if a model is provided
    if response_model:
        params["response_format"] = {"type": "json_object"}

        # Get schema information
        schema = response_model.model_json_schema()

        # Analyze schema for field types and nested objects
        field_types = {}
        nested_objects = {}

        for field, details in schema.get("properties", {}).items():
            # Determine field type
            if details.get("type") == "array":
                field_types[field] = "array"
                # Check if this is an array of objects
                items = details.get("items", {})
                if items.get("type") == "object":
                    nested_objects[field] = items.get("properties", {})
            elif details.get("type") == "number":
                field_types[field] = "number"
            elif details.get("type") == "integer":
                field_types[field] = "integer"
            elif details.get("type") == "boolean":
                field_types[field] = "boolean"
            else:
                field_types[field] = "string"

        # Format array fields and build examples for complex fields
        array_fields = [f for f, t in field_types.items() if t == "array"]
        examples = ""

        # Add special instructions for nested object arrays
        if nested_objects:
            examples = "\n\nSpecial instructions for complex fields:\n"
            for field, props in nested_objects.items():
                prop_names = list(props.keys())
                examples += f"- '{field}' must be an array of objects with these properties:\n"
                for prop in prop_names:
                    examples += f"  * '{prop}': {props[prop].get('description', '')}\n"
                
                # Add a concrete example with the correct format
                examples += f"\nExample format for '{field}':\n"
                examples += "[\n"
                examples += "  {\n"
                for prop in prop_names:
                    examples += f"    \"{prop}\": \"Example {prop} value\",\n"
                examples += "  },\n"
                examples += "  {...additional objects...}\n"
                examples += "]\n"

        # Create a guidance message with schema information
        schema_msg = (
            "Please format your response as a JSON object directly matching this schema:\n"
            f"- Required fields: {schema.get('required', [])}\n"
            "- Do not nest the response inside another object or property\n"
            f"- These fields must be arrays: {array_fields}\n"
            "- Use the correct data types for all fields\n" +
            examples
        )

        # Add schema instruction as a system message
        params["messages"].append({"role": "system", "content": schema_msg})
    else:
        # Just add a simple JSON mention if no model is provided and JSON isn't mentioned
        has_json_mention = any(
            "json" in str(m.get("content", "")).lower() for m in params["messages"]
        )
        if not has_json_mention:
            # If the last message is from the user, append to it
            if params["messages"] and params["messages"][-1]["role"] == "user":
                last_msg = params["messages"][-1]
                params["messages"][-1] = {
                    "role": "user",
                    "content": f"{last_msg['content']} Please format your response as JSON.",
                }
            # Otherwise add a new system message
            else:
                params["messages"].append(
                    {
                        "role": "system",
                        "content": "Please provide your response as JSON.",
                    }
                )

    try:
        # Always use the standard create method
        print(f"Calling OpenRouter API with params: {str(params)}")
        completion = client.chat.completions.create(**params)

        print(f"Response received. Type: {type(completion)}")

        # Check if we have valid response data
        if not completion:
            print("Error: Completion object is None")
            raise ValueError("Invalid response structure from OpenRouter - completion is None")

        if not hasattr(completion, "choices") or not completion.choices:
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
                error_msg = f"Failed to parse content as {response_model.__name__}"
                raise ValueError(f"{error_msg}: {str(parse_error)}") from parse_error
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
