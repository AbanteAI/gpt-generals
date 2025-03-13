#!/usr/bin/env python3
"""
Simple example demonstrating structured output with Pydantic models.
This example doesn't require game state and is easier to understand.
"""

import os
import sys
from typing import List, Optional

# Third-party imports
from pydantic import BaseModel, Field

# Add the repo root to the path to allow importing modules from the parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Local imports (must be after sys.path modification)
# ruff: noqa: E402
from llm_utils import Messages, call_openrouter_structured


class AnimalFact(BaseModel):
    """Model representing a fact about an animal."""

    fact: str = Field(..., description="An interesting fact about the animal")
    source: str = Field(..., description="Source or reason for knowing this fact")


class AnimalInfo(BaseModel):
    """Model for structured animal information."""

    species: str = Field(..., description="The species of the animal")
    scientific_name: str = Field(..., description="Scientific name (Latin name) of the animal")
    habitat: List[str] = Field(..., description="List of habitats where this animal can be found")
    diet: str = Field(..., description="Diet of the animal (herbivore, carnivore, omnivore, etc.)")
    lifespan_years: float = Field(..., description="Average lifespan in years")
    interesting_facts: List[AnimalFact] = Field(
        ..., description="List of interesting facts about this animal"
    )
    endangered_status: str = Field(
        ..., description="Conservation status (e.g., Least Concern, Endangered, etc.)"
    )


from typing import NamedTuple


class AnimalInfoResponse(NamedTuple):
    """Class to hold both structured animal info and raw response."""

    info: AnimalInfo
    raw_response: str


def get_animal_info(animal_name: str) -> Optional[AnimalInfoResponse]:
    """
    Get structured information about an animal using an LLM.

    Args:
        animal_name: Name of the animal to get information about

    Returns:
        AnimalInfoResponse with both structured data and raw response, or None if there was an error
    """
    messages = Messages()

    messages.add_system_message(
        "You are a wildlife expert that provides accurate information about animals."
    )

    messages.add_user_message(f"Please provide detailed information about the {animal_name}.")

    try:
        # Call the API with structured output using our AnimalInfo model
        response = call_openrouter_structured(
            messages=messages,
            response_model=AnimalInfo,
            model="openai/gpt-4o-mini",  # You can change the model as needed
        )

        # The response is a ParsedResponse when response_model is provided
        if hasattr(response, "parsed") and hasattr(response, "raw"):
            # Cast to ParsedResponse type to help the type checker
            from typing import cast

            from llm_utils import ParsedResponse

            parsed_response = cast(ParsedResponse[AnimalInfo], response)

            # Check if we received a refusal
            if parsed_response.refusal:
                print(f"Model refused to respond: {parsed_response.refusal}")
                return None

            # Response contains both parsed model and raw string (parsed is non-None here)
            return AnimalInfoResponse(info=parsed_response.parsed, raw_response=parsed_response.raw)
        else:
            # This should never happen, but satisfies the type checker
            raise TypeError("Expected ParsedResponse but got string")
    except Exception as e:
        print(f"Error getting structured animal information: {e}")
        return None


def main():
    """Run the simple structured output test."""
    print("Simple Structured Output Example\n")

    # Get animal name from command line or use default
    animal_name = sys.argv[1] if len(sys.argv) > 1 else "African Elephant"

    print(f"Getting information about: {animal_name}")
    print("Fetching data from LLM with structured output...")

    # Get structured animal information with raw response
    response = get_animal_info(animal_name)

    if response is not None:
        animal_info = response.info

        print("\n=== Structured Animal Information ===")
        print(f"Species: {animal_info.species}")
        print(f"Scientific Name: {animal_info.scientific_name}")
        print(f"Diet: {animal_info.diet}")
        print(f"Lifespan: {animal_info.lifespan_years} years")
        print(f"Endangered Status: {animal_info.endangered_status}")

        print("\nHabitats:")
        for habitat in animal_info.habitat:
            print(f"  • {habitat}")

        print("\nInteresting Facts:")
        for i, fact in enumerate(animal_info.interesting_facts, 1):
            print(f"  {i}. {fact.fact}")
            print(f"     Source: {fact.source}")

        # Demonstrate programmatic access to the structured data
        print("\nDemonstrating programmatic access:")
        if animal_info.lifespan_years > 40:
            print(f"The {animal_info.species} has a long lifespan of over 40 years!")
        else:
            years_str = f"{animal_info.lifespan_years}"
            print(f"The {animal_info.species} has a lifespan of {years_str} years.")

        # Show raw response as well
        print("\n=== Raw LLM Response ===")
        # Print just the first 300 characters if it's very long
        raw_preview = (
            (response.raw_response[:300] + "...")
            if len(response.raw_response) > 300
            else response.raw_response
        )
        print(raw_preview)
        print(f"\nTotal raw response length: {len(response.raw_response)} characters")
    else:
        print("Failed to get structured information")


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        if "OPEN_ROUTER_KEY" in str(e):
            print("\nError: OPEN_ROUTER_KEY not found!")
            print("To use this script, create a .env file in the project root with:")
            print("OPEN_ROUTER_KEY=your_api_key_here")
            print("\nOr set the environment variable directly.")
        else:
            raise
