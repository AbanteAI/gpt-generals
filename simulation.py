import argparse
import random

from game_engine import GameEngine
from map_generator import MapGenerator
from unit_movement import get_unit_move_decision


def run_simulation(num_turns: int = 10, use_custom_map: bool = False, use_llm: bool = True):
    """
    Run a simulation of the game with unit movements for a specified number of turns.

    Args:
        num_turns: Number of turns to simulate (default 10)
        use_custom_map: Whether to use a custom generated map (default False)
        use_llm: Whether to use LLM for unit movement decisions (default True)
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
    parser.add_argument("--random", action="store_true", help="Use random movement instead of LLM")

    args = parser.parse_args()

    # Use the regular text-based simulation
    run_simulation(
        num_turns=args.turns,
        use_custom_map=args.custom_map,
        use_llm=not args.random,
    )
