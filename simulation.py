import argparse
import random
from typing import Optional, Tuple, cast

from pydantic import BaseModel, Field

from game_engine import GameEngine
from llm_utils import Messages, call_openrouter
from map_generator import MapGenerator


class MoveDecision(BaseModel):
    """Model representing a move decision for a unit."""

    direction: str = Field(
        ...,
        description="Direction to move: 'up', 'down', 'left', or 'right'",
        # Add validation to ensure direction is one of the allowed values
        pattern="^(up|down|left|right)$",
    )
    reasoning: str = Field(..., description="Reasoning behind this move decision")


def calculate_manhattan_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
    """Calculate Manhattan distance between two positions."""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def get_game_state_description(game: GameEngine) -> str:
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

    return state_description


def get_unit_move_decision(game: GameEngine, unit_name: str) -> Optional[MoveDecision]:
    """
    Get a structured move decision from the LLM for a specific unit.

    Args:
        game: GameEngine instance with the current game state
        unit_name: Name of the unit to get a move decision for

    Returns:
        MoveDecision or None if there was an error
    """
    state_description = get_game_state_description(game)
    unit_position = game.units[unit_name].position

    messages = Messages()
    messages.add_system_message(
        "You are an AI controlling a unit in the GPT Generals game. "
        "Your goal is to collect coins on the map. "
        "The game is played on a grid where units can move in four directions "
        "(up, down, left, right). "
        "Water tiles (~) cannot be traversed."
    )

    messages.add_user_message(
        f"You are controlling unit {unit_name} at position {unit_position}. "
        f"Choose a direction to move (up, down, left, or right) to collect coins efficiently.\n\n"
        f"You must respond with a JSON object containing two fields:\n"
        f"- direction: one of 'up', 'down', 'left', or 'right'\n"
        f"- reasoning: a brief explanation of why you chose this direction\n\n"
        f"Game State:\n{state_description}"
    )

    try:
        import json
        from openai import OpenAI
        from dotenv import load_dotenv
        import os

        # Load environment variables (in case not loaded yet)
        load_dotenv()

        # Get API key
        api_key = os.getenv("OPEN_ROUTER_KEY")
        if not api_key:
            raise ValueError("OPEN_ROUTER_KEY environment variable must be set")

        # Initialize client
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

        # Convert messages to the format expected by the API
        openai_messages = messages.to_openai_messages()

        # Request JSON response
        completion = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=openai_messages,
            response_format={"type": "json_object"},
        )

        # Extract content
        content = completion.choices[0].message.content
        if content is None:
            raise ValueError("No content in response")

        # Parse JSON content
        response_data = json.loads(content)

        # Create MoveDecision from parsed data
        return MoveDecision(
            direction=response_data["direction"], reasoning=response_data["reasoning"]
        )
    except Exception as e:
        print(f"Error getting move decision from LLM: {e}")
        return None


def run_simulation(num_turns: int = 10, use_custom_map: bool = False, use_llm: bool = False):
    """
    Run a simulation of the game with unit movements for a specified number of turns.

    Args:
        num_turns: Number of turns to simulate (default 10)
        use_custom_map: Whether to use a custom generated map (default False)
        use_llm: Whether to use LLM for unit movement decisions (default False)
    """
    # Create a game instance, optionally with a custom map
    if use_custom_map:
        # Generate a custom map with more land for better movement
        custom_map = MapGenerator.generate_random_map(width=15, height=10, water_probability=0.15)
        game = GameEngine(map_grid=custom_map, num_coins=8)
        print("Using custom generated map")
    else:
        game = GameEngine()
        print("Using default random map")

    print(f"Initial map (Turn {game.current_turn}):")
    print(game.render_map())
    print("\n")

    directions = ["up", "down", "left", "right"]

    mode = "LLM" if use_llm else "Random"
    print(f"Running simulation with {mode} movement mode for {num_turns} turns\n")

    for turn in range(1, num_turns + 1):
        print(f"--- Turn {turn} ---")

        # Move each unit
        for unit_name in game.units:
            if use_llm:
                # Get move decision from LLM
                print(f"Consulting LLM for unit {unit_name}...")
                decision = get_unit_move_decision(game, unit_name)

                if decision:
                    direction = decision.direction
                    print(f"Unit {unit_name} reasoning: {decision.reasoning}")
                else:
                    # Fall back to random if LLM fails
                    direction = random.choice(directions)
                    print(f"LLM failed, Unit {unit_name} choosing random direction.")
            else:
                # Use random movement
                direction = random.choice(directions)

            success = game.move_unit(unit_name, direction)
            result = "Success" if success else "Failed"
            print(f"Unit {unit_name} attempts to move {direction}: {result}")

        # Advance to next turn
        game.next_turn()

        # Display the updated map
        print(f"\nMap after Turn {game.current_turn - 1}:")
        print(game.render_map())
        print("\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a GPT Generals simulation.")
    parser.add_argument("--turns", type=int, default=10, help="Number of turns to simulate")
    parser.add_argument("--custom-map", action="store_true", help="Use a custom map")
    parser.add_argument("--llm", action="store_true", help="Use LLM for unit movement decisions")

    args = parser.parse_args()

    run_simulation(num_turns=args.turns, use_custom_map=args.custom_map, use_llm=args.llm)
