#!/usr/bin/env python3
"""
Simple example demonstrating structured output with Pydantic models.
This example doesn't require game state and is easier to understand.
"""

import os
import sys
from typing import List, Optional

from pydantic import BaseModel, Field

# Add parent directory to path to import modules from root
# This works both when run directly and when the script is in a subdirectory
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
sys.path.insert(0, repo_root)

# Now we can import modules from the root directory
from llm_utils import Messages, call_openrouter


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


def get_animal_info(animal_name: str) -> Optional[AnimalInfo]:
    """
    Get structured information about an animal using an LLM.

    Args:
        animal_name: Name of the animal to get information about

    Returns:
        AnimalInfo or None if there was an error
    """
    messages = Messages()

    messages.add_system_message(
        "You are a wildlife expert that provides accurate information about animals."
    )

    messages.add_user_message(f"Please provide detailed information about the {animal_name}.")

    try:
        # Call the API with structured output using our AnimalInfo model
        animal_info = call_openrouter(
            messages=messages,
            model="openai/gpt-4o-mini",  # You can change the model as needed
            response_model=AnimalInfo,
        )

        # Since we specified the response_model, we know this is an AnimalInfo object
        return animal_info  # type: ignore
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

    # Get structured animal information
    animal_info = get_animal_info(animal_name)

    if animal_info is not None and isinstance(animal_info, AnimalInfo):
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
    else:
        print("Failed to get structured information")


if __name__ == "__main__":
    main()
