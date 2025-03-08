#!/usr/bin/env python3
# ruff: noqa: E402
"""
Simulation script for the GPT Generals game with random movements.
"""

import os
import random
import sys

# Add the repo root to the path to allow importing modules from the parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Local imports - after path setup
from game_engine import GameEngine
from map_generator import MapGenerator


def run_simulation(num_turns: int = 10, use_custom_map: bool = False):
    """
    Run a simulation of the game with random unit movements for a specified number of turns.

    Args:
        num_turns: Number of turns to simulate (default 10)
        use_custom_map: Whether to use a custom generated map (default False)
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

    for turn in range(1, num_turns + 1):
        print(f"--- Turn {turn} ---")

        # Move each unit randomly
        for unit_name in game.units:
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
    # Run a simulation with default settings
    run_simulation()

    # Uncomment to run with a custom map
    # run_simulation(use_custom_map=True)
