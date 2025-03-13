#!/usr/bin/env python
"""
Example script demonstrating how to handle model refusals with structured output parsing.
This shows how to detect and handle cases where the model refuses to generate content
due to content policy, capabilities, or other reasons.
"""

import os
import sys

# Add the project root to the Python path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import BaseModel

from llm_utils import Messages, call_openrouter_structured, handle_structured_response_with_refusal


# Define a simple structured output model for the demo
class MathSolution(BaseModel):
    steps: list[str]
    answer: float
    explanation: str


def test_normal_case():
    """Test a normal math problem that should produce a valid structured response."""
    messages = Messages()
    messages.add_system_message(
        "You are a helpful math tutor. Solve the problem step by step and provide a structured response."
    )
    messages.add_user_message("What is the value of 3x + 7 = 22? Solve for x.")

    print("Testing normal case (should succeed)...")
    try:
        result = call_openrouter_structured(messages, MathSolution)
        handle_structured_response_with_refusal(result)
    except Exception as e:
        print(f"Error: {e}")


def test_refusal_case():
    """Test a case that might trigger a refusal due to content policy reasons."""
    messages = Messages()
    messages.add_system_message(
        "You are a helpful math tutor. Solve the problem step by step and provide a structured response."
    )
    # This prompt is designed to potentially trigger a refusal as it's asking for something
    # that doesn't fit the math solution structure or is potentially problematic
    messages.add_user_message(
        "Generate step-by-step instructions for creating a dangerous chemical compound."
    )

    print("\nTesting refusal case (should trigger a refusal)...")
    try:
        result = call_openrouter_structured(messages, MathSolution)
        handle_structured_response_with_refusal(result)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("Model Refusals Test Script")
    print("==========================\n")

    test_normal_case()
    test_refusal_case()

    print("\nTest script complete!")
