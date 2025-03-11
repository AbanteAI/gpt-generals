#!/usr/bin/env python3
"""
Test script for demonstrating structured output with Pydantic models.
"""

import os
import sys
from typing import Dict, List, Optional, cast

# Third-party imports
from pydantic import BaseModel, Field

# Add the repo root to the path to allow importing modules from the parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Local imports (must be after sys.path modification)
# ruff: noqa: E402
from game_engine import GameEngine
from llm_utils import Messages, call_openrouter
from map_generator import MapGenerator


class Move(BaseModel):
    """Model representing a move recommendation for a unit."""

    unit_name: str = Field(..., description="Name of the unit to move")
    direction: str = Field(..., description="Direction to move: 'up', 'down', 'left', or 'right'")
    reason: str = Field(..., description="Reasoning behind this move recommendation")


class GameAnalysis(BaseModel):
    """Model for structured game analysis output."""

    situation_assessment: str = Field(..., description="Assessment of the current game situation")
    recommended_moves: List[Move] = Field(..., description="List of recommended moves for units")
    coin_proximity: Dict[str, int] = Field(..., description="Distance of each unit to nearest coin")
    winning_probability: float = Field(
        ...,
        description="Estimated probability of winning from this position (0.0 to 1.0)",
        ge=0.0,
        le=1.0,
    )


def calculate_manhattan_distance(pos1, pos2):
    """Calculate Manhattan distance between two positions."""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def get_game_state_description(game):
    """Generate a text description of the current game state."""
    map_render = game.render_map()

    # Get unit positions
    unit_positions = {}
    for name, unit in game.units.items():
        unit_positions[name] = unit.position

    # Calculate distances to nearest coins
    coin_distances = {}
    for name, unit in game.units.items():
        distances = [
            calculate_manhattan_distance(unit.position, coin_pos)
            for coin_pos in game.coin_positions
        ]
        nearest_distance = min(distances) if distances else -1
        coin_distances[name] = nearest_distance

    # Create game state description
    state_description = f"""
Current Game State:
{map_render}

Unit Positions:
{", ".join([f"{name} at {pos}" for name, pos in unit_positions.items()])}

Coins: {len(game.coin_positions)} remaining at {game.coin_positions}

Turn: {game.current_turn}
    """

    return state_description, coin_distances


def get_structured_game_analysis(game) -> Optional[GameAnalysis]:
    """
    Get a structured analysis of the current game state using the LLM.

    Args:
        game: GameEngine instance with the current game state

    Returns:
        GameAnalysis or None if there was an error
    """
    state_description, coin_distances = get_game_state_description(game)

    messages = Messages()
    messages.add_system_message(
        "You are a game AI analyst that provides strategic advice for the GPT Generals game. "
        "The game is played on a grid where units can move in four directions "
        "(up, down, left, right). "
        "Units collect coins on the map. Water tiles cannot be traversed."
    )

    messages.add_user_message(
        f"Analyze this game state and provide strategic advice:\n\n{state_description}"
    )

    try:
        # Call the API with structured output using our GameAnalysis model
        analysis = call_openrouter(
            messages=messages,
            model="openai/gpt-4o-mini",  # You can change the model as needed
            response_model=GameAnalysis,
        )

        # Since we specified the response_model, we know this is a GameAnalysis object
        return cast(GameAnalysis, analysis)
    except Exception as e:
        print(f"Error getting structured analysis: {e}")
        return None


def main():
    """Run the structured output test."""
    print("Testing structured output with Pydantic models\n")

    # Create a game instance with a custom map for better demonstration
    custom_map = MapGenerator.generate_random_map(width=8, height=6, water_probability=0.2)
    game = GameEngine(map_grid=custom_map, num_coins=4)

    print("Game State:")
    print(game.render_map())
    print("\nGetting structured analysis from LLM...")

    # Get structured analysis
    analysis = get_structured_game_analysis(game)

    if analysis is not None and isinstance(analysis, GameAnalysis):
        print("\n=== Structured Analysis Results ===")
        print(f"Situation Assessment: {analysis.situation_assessment}")

        print("\nRecommended Moves:")
        for move in analysis.recommended_moves:
            print(f"  • {move.unit_name}: Move {move.direction} - {move.reason}")

        print("\nCoin Proximity:")
        for unit, distance in analysis.coin_proximity.items():
            print(f"  • {unit}: {distance} steps from nearest coin")

        print(f"\nWinning Probability: {analysis.winning_probability:.2f}")

        # Show that we can access the fields programmatically
        print("\nAccessing fields programmatically:")
        # Sort moves by unit name
        sorted_moves = sorted(analysis.recommended_moves, key=lambda m: m.unit_name)
        for move in sorted_moves:
            print(f"Unit {move.unit_name} should move {move.direction}")
    else:
        print("Failed to get structured analysis")


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
