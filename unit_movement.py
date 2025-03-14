from enum import Enum
from typing import NamedTuple, Optional

from pydantic import BaseModel, Field

from game_engine import GameEngine
from llm_utils import Messages, call_openrouter_structured
from map_generator import TerrainType


class Direction(str, Enum):
    """Enum for the valid move directions."""

    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class MoveDecision(BaseModel):
    """Model representing a move decision for a unit."""

    reasoning: str = Field(..., description="Reasoning behind this move decision")
    direction: Direction = Field(
        ...,
        description="Direction to move: 'up', 'down', 'left', or 'right'",
    )


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
        primary_direction describes the overall direction
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
            # Instead of using directions like "up-left", use "X left, Y up" format
            x_direction = "left" if "left" in direction else "right" if "right" in direction else ""
            y_direction = "up" if "up" in direction else "down" if "down" in direction else ""

            if x_dist > 0 and y_dist > 0:
                direction_desc = f"{x_dist} {x_direction}, {y_dist} {y_direction}"
            elif x_dist > 0:
                direction_desc = f"{x_dist} {x_direction}"
            else:
                direction_desc = f"{y_dist} {y_direction}"

            surroundings.append(f"The closest coin is {distance} steps away ({direction_desc}).")

        # Mention other coins
        if len(nearby_coins) > 1:
            other_coins_text = []
            # Limit to 3 more coins
            for _i, (_coin_pos, distance, _direction, x_dist, y_dist) in enumerate(
                nearby_coins[1:4]
            ):
                # Use the same "X left, Y up" format for other coins
                x_direction = (
                    "left" if "left" in _direction else "right" if "right" in _direction else ""
                )
                y_direction = "up" if "up" in _direction else "down" if "down" in _direction else ""

                if x_dist > 0 and y_dist > 0:
                    direction_desc = f"{x_dist} {x_direction}, {y_dist} {y_direction}"
                elif x_dist > 0:
                    direction_desc = f"{x_dist} {x_direction}"
                else:
                    direction_desc = f"{y_dist} {y_direction}"

                other_coins_text.append(f"another coin {distance} steps away ({direction_desc})")

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
                    water_tiles.append((pos, distance, direction, x_dist, y_dist))

    # Sort water by distance
    water_tiles.sort(key=lambda x: x[1])

    # Describe water obstacles
    if water_tiles:
        water_directions = []
        for _pos, distance, _direction, x_dist, y_dist in water_tiles[:3]:  # Limit to 3 water tiles
            # Use the same "X left, Y up" format for water
            x_direction = (
                "left" if "left" in _direction else "right" if "right" in _direction else ""
            )
            y_direction = "up" if "up" in _direction else "down" if "down" in _direction else ""

            if x_dist > 0 and y_dist > 0:
                direction_desc = f"{x_dist} {x_direction}, {y_dist} {y_direction}"
            elif x_dist > 0:
                direction_desc = f"{x_dist} {x_direction}"
            else:
                direction_desc = f"{y_dist} {y_direction}"

            water_directions.append(
                f"{direction_desc} ({distance} step{'s' if distance > 1 else ''})"
            )

        water_desc = ", ".join(water_directions)
        surroundings.append(f"Watch out for water {water_desc}.")

    # Find other units
    other_units = []
    for name, unit in game.units.items():
        if name != unit_name:
            pos = unit.position
            distance = calculate_manhattan_distance(unit_position, pos)
            direction, x_dist, y_dist = get_relative_direction(unit_position, pos)
            other_units.append((name, pos, distance, direction, x_dist, y_dist))

    # Describe other units
    for name, _pos, distance, _direction, x_dist, y_dist in other_units:
        # Use the same "X left, Y up" format for other units
        x_direction = "left" if "left" in _direction else "right" if "right" in _direction else ""
        y_direction = "up" if "up" in _direction else "down" if "down" in _direction else ""

        if x_dist > 0 and y_dist > 0:
            direction_desc = f"{x_dist} {x_direction}, {y_dist} {y_direction}"
        elif x_dist > 0:
            direction_desc = f"{x_dist} {x_direction}"
        else:
            direction_desc = f"{y_dist} {y_direction}"

        surroundings.append(f"Unit {name} is {distance} steps away ({direction_desc}).")

    # Check borders
    borders = []
    if unit_position[0] == 0:
        borders.append("left")
    if unit_position[0] == len(game.map_grid[0]) - 1:
        borders.append("right")
    if unit_position[1] == 0:
        borders.append("bottom")
    if unit_position[1] == len(game.map_grid) - 1:
        borders.append("top")

    if borders:
        borders_text = " and ".join(borders)
        surroundings.append(f"You're at the {borders_text} edge of the map.")

    return "\n".join(surroundings)


def get_game_state_description(game: GameEngine) -> str:
    """Generate a text description of the current game state."""
    # Get the map rendering
    full_map_render = game.render_map()

    # Remove row and column numbers from the map render
    map_lines = full_map_render.split("\n")
    map_render_no_coords = []

    # Skip the first line (column numbers)
    for line in map_lines[1:]:
        # Skip the first 2 characters (row number and space)
        map_render_no_coords.append(line[2:])

    map_render = "\n".join(map_render_no_coords)

    # Get unit positions
    unit_positions = {}
    for name, unit in game.units.items():
        unit_positions[name] = unit.position

    # Add explanation of symbols
    symbol_explanation = """
Map symbols:
. = Land (movable)
~ = Water (not movable)
A, B, etc. = Units (on the same team)
c = Coin (collect these)
"""

    # Create game state description
    state_description = f"""
Current state of the map:
{map_render}
{symbol_explanation}
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
        "to help you understand where coins, water, and other units are relative to your position. "
        "Units A and B are on the same team and should work together to collect coins efficiently."
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

            # Check if we received a refusal
            if parsed_response.refusal:
                print(f"Model refused to respond: {parsed_response.refusal}")
                return None

            # Return both the parsed model and raw response
            assert parsed_response.parsed is not None  # Help type checker
            return MoveDecisionResponse(
                decision=parsed_response.parsed, raw_response=parsed_response.raw
            )
        else:
            # This should never happen, but satisfies the type checker
            raise TypeError("Expected ParsedResponse but got string")
    except Exception as e:
        print(f"Error getting move decision from LLM: {e}")
        return None
