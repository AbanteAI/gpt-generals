#!/usr/bin/env python3
"""
Simulation script for the GPT Generals game.

This script is a simple wrapper that runs the simulation from the root simulation.py file.
It defaults to using LLM-based movement, but can also use random movement with the --random flag.
"""

import argparse
import os
import sys

# Add the repo root to the path to allow importing modules from the parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Local imports (must be after sys.path modification)
# ruff: noqa: E402
from simulation import run_simulation


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
