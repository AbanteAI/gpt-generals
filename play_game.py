#!/usr/bin/env python3
"""
Main script for playing GPT Generals with manual input.
"""

import argparse
from game_engine import GameEngine
from player_controller import PlayerController


def main():
    """Run the main game loop for playing GPT Generals with manual input."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Play GPT Generals with manual control")
    parser.add_argument("--width", type=int, default=10, help="Width of the map")
    parser.add_argument("--height", type=int, default=10, help="Height of the map")
    parser.add_argument("--water", type=float, default=0.2, help="Probability of water tiles")
    parser.add_argument("--coins", type=int, default=5, help="Number of coins on the map")

    args = parser.parse_args()

    # Create game instance
    game = GameEngine(
        width=args.width,
        height=args.height,
        water_probability=args.water,
        num_coins=args.coins
    )

    # Create player controller
    controller = PlayerController(game)

    # Game loop
    print("Welcome to GPT Generals!")
    print("Controls: <unit_letter><direction> (e.g., 'Aw' to move unit A up)")
    print("Directions: w (up), a (left), s (down), d (right)")
    print("Type 'quit' or 'q' to exit")

    coins_collected = 0
    total_coins = len(game.coin_positions)

    while True:
        # Display game state
        print(f"\nTurn {game.current_turn}:")
        print(game.render_map())

        # Display unit positions
        print("\nUnit positions:")
        for name, unit in game.units.items():
            print(f"  Unit {name}: {unit.position}")

        print(f"Coins remaining: {len(game.coin_positions)} / {total_coins}")

        # Check win condition
        if not game.coin_positions:
            print("\nCongratulations! You've collected all coins.")
            print(f"Game completed in {game.current_turn} turns.")
            break

        # Get player input
        player_input = input("\nEnter move or 'q' to quit: ").strip().lower()

        # Check for quit command
        if player_input in ['q', 'quit']:
            print("\nGame ended.")
            print(f"Turns played: {game.current_turn}")
            print(f"Coins collected: {total_coins - len(game.coin_positions)} / {total_coins}")
            break

        # Check for help command
        if player_input in ['h', 'help']:
            print("\nControls: <unit_letter><direction>")
            print("  Unit letter: A, B, etc.")
            print("  Direction: w (up), a (left), s (down), d (right)")
            print("Examples: 'Aw' moves unit A up, 'Bd' moves unit B right")
            print("Commands: 'q' to quit, 'h' for help")
            continue

        # Process input
        if controller.process_input(player_input):
            prev_coins = len(game.coin_positions)
            # Check if a coin was collected this turn
            if prev_coins > len(game.coin_positions):
                print("Coin collected!")
                coins_collected += 1

            # Move was successful, advance to next turn
            game.next_turn()


if __name__ == "__main__":
    main()
