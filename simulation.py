import argparse
import json
import os
import random
from typing import Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

from game_engine import GameEngine
from llm_utils import Messages
from map_generator import MapGenerator, TerrainType


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


def get_nearby_description(game: GameEngine, unit_name: str) -> str:
    """Generate a natural language description of what's around a unit."""
    unit = game.units[unit_name]
    x, y = unit.position

    # Define directions (up, down, left, right) and their offsets
    directions = {
        "north": (0, -1),  # Up (decreasing y)
        "south": (0, 1),  # Down (increasing y)
        "west": (-1, 0),  # Left (decreasing x)
        "east": (1, 0),  # Right (increasing x)
    }

    # Get map dimensions for boundary checking
    max_x = game.width - 1
    max_y = game.height - 1

    # Generate descriptions for each direction
    nearby_descriptions = []
    coin_directions = []

    for direction_name, (dx, dy) in directions.items():
        new_x, new_y = x + dx, y + dy

        # Check if the position is within map boundaries
        if 0 <= new_x <= max_x and 0 <= new_y <= max_y:
            terrain = game.map_grid[new_y][new_x]
            if terrain == TerrainType.WATER:
                nearby_descriptions.append(f"There is water to the {direction_name}.")
            else:  # It's land
                nearby_descriptions.append(f"There is land to the {direction_name}.")

                # Check if there's a unit at this position
                unit_at_pos = None
                for other_name, other_unit in game.units.items():
                    if other_unit.position == (new_x, new_y):
                        unit_at_pos = other_name
                        break

                if unit_at_pos:
                    nearby_descriptions.append(f"Unit {unit_at_pos} is to the {direction_name}.")

                # Check if there's a coin at this position
                if (new_x, new_y) in game.coin_positions:
                    coin_directions.append(direction_name)
        else:
            nearby_descriptions.append(f"You can't go {direction_name} (map edge).")

    # Add coin information
    if coin_directions:
        if len(coin_directions) == 1:
            nearby_descriptions.append(f"There is a coin to the {coin_directions[0]}!")
        else:
            coin_list = ", ".join(coin_directions[:-1]) + f" and {coin_directions[-1]}"
            nearby_descriptions.append(f"There are coins to the {coin_list}!")

    # Find nearest coins beyond adjacent cells
    non_adjacent_coins = [
        pos for pos in game.coin_positions if abs(pos[0] - x) > 1 or abs(pos[1] - y) > 1
    ]

    if non_adjacent_coins:
        # Find the nearest non-adjacent coin
        distances = [(calculate_manhattan_distance((x, y), pos), pos) for pos in non_adjacent_coins]
        min_distance, nearest_coin = min(distances)
        coin_x, coin_y = nearest_coin

        # Generate direction hint
        direction_hint = []
        if coin_y < y:
            direction_hint.append("north")
        elif coin_y > y:
            direction_hint.append("south")

        if coin_x < x:
            direction_hint.append("west")
        elif coin_x > x:
            direction_hint.append("east")

        direction_str = "-".join(direction_hint) if direction_hint else "unknown direction"
        nearby_descriptions.append(
            f"The nearest coin is {min_distance} steps away to the {direction_str}."
        )

    return "\n".join(nearby_descriptions)


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
    nearby_description = get_nearby_description(game, unit_name)

    messages = Messages()
    messages.add_system_message(
        "You are an AI controlling a unit in the GPT Generals game. "
        "Your goal is to collect coins on the map. "
        "The game is played on a grid where units can move in four directions "
        "(up, down, left, right). "
        "The map is displayed with row 0 at the bottom and higher rows at the top. "
        "Up means moving toward the top of the displayed map (decreasing y-coordinate), "
        "Down means moving toward the bottom of the displayed map (increasing y-coordinate), "
        "Left means moving toward the left of the map (decreasing x-coordinate), "
        "Right means moving toward the right of the map (increasing x-coordinate). "
        "Water tiles (~) cannot be traversed. "
        "You will receive natural language descriptions of your surroundings "
        "to help you understand where coins, water, and other units are relative to your position."
    )

    messages.add_user_message(
        f"You are controlling unit {unit_name} at position {unit_position}. "
        f"Choose a direction to move (up, down, left, or right) to collect coins efficiently.\n\n"
        f"You must respond with a JSON object containing two fields:\n"
        f"- direction: one of 'up', 'down', 'left', or 'right'\n"
        f"- reasoning: a brief explanation of why you chose this direction\n\n"
        f"What's around you:\n{nearby_description}\n\n"
        f"Game State:\n{state_description}"
    )

    try:
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
