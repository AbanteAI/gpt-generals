#!/usr/bin/env python3
"""
Simulation script for the GPT Generals game.

This script can run simulations with either LLM-based movement (default) or random movement.
"""

import argparse
import os
import random
import sys

# Add the repo root to the path to allow importing modules from the parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Local imports (must be after sys.path modification)
# ruff: noqa: E402
from game_engine import GameEngine
from map_generator import MapGenerator


def run_simulation(num_turns: int = 10, use_custom_map: bool = False, use_llm: bool = True):
    """
    Run a simulation of the game with either LLM-based or random unit movements.

    Args:
        num_turns: Number of turns to simulate (default 10)
        use_custom_map: Whether to use a custom generated map (default False)
        use_llm: Whether to use LLM for movement decisions (default True)
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

    movement_type = "LLM-based" if use_llm else "random"
    print(f"Running simulation with {movement_type} movement")

    print(f"Initial map (Turn {game.current_turn}):")
    print(game.render_map())
    print("\n")

    directions = ["up", "down", "left", "right"]

    for turn in range(1, num_turns + 1):
        print(f"--- Turn {turn} ---")

        # Move each unit
        for unit_name in game.units:
            # Get movement direction (either from LLM or random)
            if use_llm:
                # Just use random for now, but later this will use LLM
                direction = random.choice(directions)
            else:
                direction = random.choice(directions)

            # Try to move the unit
            success = game.move_unit(unit_name, direction)
            result = "Success" if success else "Failed"
            print(f"Unit {unit_name} attempts to move {direction}: {result}")

        # Advance to next turn
        game.next_turn()

        # Display the updated map
        print(f"\nMap after Turn {game.current_turn - 1}:")
        print(game.render_map())
        print("\n")


def main():
    """Parse command-line arguments and run the simulation."""
    parser = argparse.ArgumentParser(
        description="Run a GPT Generals simulation with LLM-directed or random movement."
    )
    parser.add_argument(
        "--turns", type=int, default=5, help="Number of turns to simulate (default: 5)"
    )
    parser.add_argument(
        "--random", action="store_true", help="Use random movement instead of LLM (default: False)"
    )
    parser.add_argument(
        "--custom-map", action="store_true", help="Use a custom map with more land and coins"
    )

    args = parser.parse_args()

    # Display banner
    print("=" * 70)
    print("GPT Generals Simulation")
    print("=" * 70)

    # Run simulation with LLM-based movement unless --random flag is used
    use_llm = not args.random

    try:
        run_simulation(num_turns=args.turns, use_custom_map=args.custom_map, use_llm=use_llm)
        print("\nSimulation completed successfully!")
    except ValueError as e:
        if "OPEN_ROUTER_KEY" in str(e):
            print("\nError: OPEN_ROUTER_KEY not found!")
            print("To use this script, create a .env file in the project root with:")
            print("OPEN_ROUTER_KEY=your_api_key_here")
            print("\nOr set the environment variable directly.")
        else:
            raise


if __name__ == "__main__":
    main()
