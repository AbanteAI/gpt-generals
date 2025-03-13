import argparse
import random
from typing import NamedTuple, Optional

from pydantic import BaseModel, Field

from game_engine import GameEngine
from llm_utils import Messages, call_openrouter_structured
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


class MoveDecisionResponse(NamedTuple):
    """Class to hold both structured move decision and raw response."""

    decision: MoveDecision
    raw_response: str


def calculate_manhattan_distance(pos1: tuple[int, int], pos2: tuple[int, int]) -> int:
    """Calculate Manhattan distance between two positions."""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def get_relative_direction(
    from_pos: tuple[int, int], to_pos: tuple[int, int]
) -> tuple[str, int, int]:
    """
    Get the relative direction from one position to another.

    Args:
        from_pos: Starting position (x, y)
        to_pos: Target position (x, y)

    Returns:
        Tuple of (primary_direction, x_distance, y_distance)
        primary_direction is one of: "up", "down", "left", "right", or a combination like "up-left"
    """
    x_diff = to_pos[0] - from_pos[0]
    y_diff = to_pos[1] - from_pos[1]

    x_distance = abs(x_diff)
    y_distance = abs(y_diff)

    # Determine primary directions
    x_direction = "right" if x_diff > 0 else "left" if x_diff < 0 else ""
    y_direction = "up" if y_diff > 0 else "down" if y_diff < 0 else ""

    # Combine directions
    if x_direction and y_direction:
        primary_direction = f"{y_direction}-{x_direction}"
    elif x_direction:
        primary_direction = x_direction
    else:
        primary_direction = y_direction

    return primary_direction, x_distance, y_distance


def get_unit_surroundings(game: GameEngine, unit_name: str) -> str:
    """
    Create a human-friendly description of what surrounds the unit.

    Args:
        game: GameEngine instance with the current game state
        unit_name: Name of the unit to describe surroundings for

    Returns:
        A string describing what's around the unit in intuitive terms
    """
    unit_position = game.units[unit_name].position
    surroundings = []

    # Find nearby coins (all coins sorted by distance)
    nearby_coins = []
    for coin_pos in game.coin_positions:
        distance = calculate_manhattan_distance(unit_position, coin_pos)
        direction, x_dist, y_dist = get_relative_direction(unit_position, coin_pos)
        nearby_coins.append((coin_pos, distance, direction, x_dist, y_dist))

    # Sort coins by distance
    nearby_coins.sort(key=lambda x: x[1])

    # Describe coins
    if nearby_coins:
        # Describe closest coin with detailed directions
        closest = nearby_coins[0]
        coin_pos, distance, direction, x_dist, y_dist = closest
        if distance == 1:
            surroundings.append(f"There's a coin right {direction} from you.")
        else:
            surroundings.append(
                f"The closest coin is {distance} steps away {direction} "
                f"({y_dist} {('step' if y_dist == 1 else 'steps')} "
                f"{'up' if 'up' in direction else 'down' if 'down' in direction else ''}"
                f"{' and ' if 'up' in direction or 'down' in direction else ''}"
                f"{x_dist} {('step' if x_dist == 1 else 'steps')} "
                f"{'left' if 'left' in direction else 'right' if 'right' in direction else ''}"
                f")."
            )

        # Mention other coins
        if len(nearby_coins) > 1:
            other_coins_text = []
            # Limit to 3 more coins
            for _i, (_coin_pos, distance, direction, _x_dist, _y_dist) in enumerate(
                nearby_coins[1:4]
            ):
                other_coins_text.append(f"another coin {distance} steps away {direction}")

            if other_coins_text:
                more_coins = len(nearby_coins) - 4 if len(nearby_coins) > 4 else 0
                coins_desc = ", ".join(other_coins_text)
                if more_coins > 0:
                    coins_desc += f", and {more_coins} more farther away"
                surroundings.append(f"There's also {coins_desc}.")
    else:
        surroundings.append("There are no coins on the map.")

    # Find nearby water obstacles (within 3 steps)
    water_tiles = []
    for y in range(max(0, unit_position[1] - 3), min(len(game.map_grid), unit_position[1] + 4)):
        x_range = range(
            max(0, unit_position[0] - 3), min(len(game.map_grid[0]), unit_position[0] + 4)
        )
        for x in x_range:
            if game.map_grid[y][x] == TerrainType.WATER:
                pos = (x, y)
                distance = calculate_manhattan_distance(unit_position, pos)
                if distance <= 3:  # Only consider water within 3 steps
                    direction, x_dist, y_dist = get_relative_direction(unit_position, pos)
                    water_tiles.append((pos, distance, direction))

    # Sort water by distance
    water_tiles.sort(key=lambda x: x[1])

    # Describe water obstacles
    if water_tiles:
        water_directions = []
        for _pos, distance, direction in water_tiles[:3]:  # Limit to 3 water tiles
            water_directions.append(f"{direction} ({distance} step{'s' if distance > 1 else ''})")

        water_desc = ", ".join(water_directions)
        surroundings.append(f"Watch out for water {water_desc}.")

    # Find other units
    other_units = []
    for name, unit in game.units.items():
        if name != unit_name:
            pos = unit.position
            distance = calculate_manhattan_distance(unit_position, pos)
            direction, x_dist, y_dist = get_relative_direction(unit_position, pos)
            other_units.append((name, pos, distance, direction))

    # Describe other units
    for name, _pos, distance, direction in other_units:
        surroundings.append(f"Unit {name} is {distance} steps away {direction}.")

    # Check borders
    borders = []
    if unit_position[0] == 0:
        borders.append("western")
    if unit_position[0] == len(game.map_grid[0]) - 1:
        borders.append("eastern")
    if unit_position[1] == 0:
        borders.append("northern")
    if unit_position[1] == len(game.map_grid) - 1:
        borders.append("southern")

    if borders:
        borders_text = " and ".join(borders)
        surroundings.append(f"You're at the {borders_text} edge of the map.")

    return "\n".join(surroundings)


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


def get_unit_move_decision(game: GameEngine, unit_name: str) -> Optional[MoveDecisionResponse]:
    """
    Get a structured move decision from the LLM for a specific unit.

    Args:
        game: GameEngine instance with the current game state
        unit_name: Name of the unit to get a move decision for

    Returns:
        MoveDecisionResponse with both structured decision and raw response,
        or None if there was an error
    """
    state_description = get_game_state_description(game)
    unit_position = game.units[unit_name].position

    # Get intuitive description of the unit's surroundings
    surroundings_description = get_unit_surroundings(game, unit_name)

    messages = Messages()
    messages.add_system_message(
        "You are an AI controlling a unit in the GPT Generals game. "
        "Your goal is to collect coins on the map. "
        "The game is played on a grid where units can move in four directions "
        "(up, down, left, right). "
        "Water tiles (~) cannot be traversed. "
        "You will receive natural language descriptions of your surroundings "
        "to help you understand where coins, water, and other units are relative to your position."
    )

    messages.add_user_message(
        f"You are controlling unit {unit_name} at position {unit_position}. "
        f"Choose a direction to move (up, down, left, or right) to collect coins efficiently.\n\n"
        f"Your surroundings:\n{surroundings_description}\n\n"
        f"You must respond with a JSON object containing two fields:\n"
        f"- direction: one of 'up', 'down', 'left', or 'right'\n"
        f"- reasoning: a brief explanation of why you chose this direction\n\n"
        f"Game State (for reference):\n{state_description}"
    )

    try:
        # Call the API with structured output using our MoveDecision model
        response = call_openrouter_structured(
            messages=messages,
            response_model=MoveDecision,
            model="openai/gpt-4o-mini",
        )

        # The response is a ParsedResponse when response_model is provided
        if hasattr(response, "parsed") and hasattr(response, "raw"):
            # Cast to ParsedResponse type to help the type checker
            from typing import cast

            from llm_utils import ParsedResponse

            parsed_response = cast(ParsedResponse[MoveDecision], response)

            # Return both the parsed model and raw response
            return MoveDecisionResponse(
                decision=parsed_response.parsed, raw_response=parsed_response.raw
            )
        else:
            # This should never happen, but satisfies the type checker
            raise TypeError("Expected ParsedResponse but got string")
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
                response = get_unit_move_decision(game, unit_name)

                if response:
                    direction = response.decision.direction
                    print(f"Unit {unit_name} reasoning: {response.decision.reasoning}")

                    # Debug information about raw response (can be commented out in production)
                    if len(response.raw_response) > 200:
                        raw_preview = response.raw_response[:200] + "..."
                    else:
                        raw_preview = response.raw_response
                    print(f"Raw response preview: {raw_preview}")
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

    # Use the regular text-based simulation
    run_simulation(
        num_turns=args.turns,
        use_custom_map=args.custom_map,
        use_llm=args.llm,
    )
