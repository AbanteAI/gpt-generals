#!/usr/bin/env python3
"""
Main script for playing GPT Generals with manual or natural language input.
"""

import argparse

from game_engine import GameEngine
from player_controller import PlayerController


def main():
    """Run the main game loop for playing GPT Generals with manual or natural language input."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Play GPT Generals")
    parser.add_argument("--width", type=int, default=10, help="Width of the map")
    parser.add_argument("--height", type=int, default=10, help="Height of the map")
    parser.add_argument("--water", type=float, default=0.2, help="Probability of water tiles")
    parser.add_argument("--coins", type=int, default=5, help="Number of coins on the map")
    parser.add_argument("--tui", action="store_true", help="Use terminal UI instead of text mode")
    parser.add_argument(
        "--manual", action="store_true", help="Use manual control mode (unit/direction commands)"
    )

    args = parser.parse_args()

    # Create game instance
    game = GameEngine(
        width=args.width,
        height=args.height,
        water_probability=args.water,
        num_coins=args.coins,
    )

    # Check if we should use the TUI
    if args.tui:
        from player_tui import run_player_tui

        run_player_tui(game, manual_mode=args.manual)
        return

    # Create player controller for text mode
    controller = PlayerController(game, manual_mode=args.manual)

    # Game loop
    print("Welcome to GPT Generals!")
    if args.manual:
        print("MANUAL MODE: Use <unit_letter><direction> format (e.g., 'Aw' to move unit A up)")
        print("Directions: w/k (up), a/h (left), s/j (down), d/l (right)")
    else:
        print("CHAT MODE: Type natural language commands to communicate with units")
        print("Type 'toggle' to switch between chat and manual modes")
    print("Type 'quit' or 'q' to exit, 'h' or 'help' for help")

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

        # Show recent chat history in non-manual mode
        if not controller.manual_mode:
            print("\nChat History:")
            print(controller.get_chat_history(max_messages=5))

        # Check win condition
        if not game.coin_positions:
            print("\nCongratulations! You've collected all coins.")
            print(f"Game completed in {game.current_turn} turns.")
            break

        # Get player input
        prompt = "\nEnter move or command: " if controller.manual_mode else "\nEnter message: "
        player_input = input(prompt).strip()

        # Convert to lowercase only in manual mode
        if controller.manual_mode:
            player_input = player_input.lower()

        # Check for quit command
        if player_input.lower() in ["q", "quit"]:
            print("\nGame ended.")
            print(f"Turns played: {game.current_turn}")
            print(f"Coins collected: {total_coins - len(game.coin_positions)} / {total_coins}")
            break

        # Check for help command
        if player_input.lower() in ["h", "help"]:
            if controller.manual_mode:
                print("\nManual Mode Controls:")
                print(
                    "  Unit letter + Direction: A, B, etc. + w/k (up), a/h (left), s/j (down), d/l (right)"
                )
                print("  Examples: 'Aw' moves unit A up, 'Bd' moves unit B right")
            else:
                print("\nChat Mode:")
                print("  Type natural language commands to interact with units")
                print("  Examples: 'Unit A move north', 'Unit B collect the coin to your right'")
            print("\nGeneral Commands:")
            print("  'toggle': Switch between manual and chat modes")
            print("  'q' or 'quit': Exit the game")
            print("  'h' or 'help': Show this help message")
            continue

        # Check for mode toggle
        if player_input.lower() == "toggle":
            controller.toggle_mode()
            continue

        # Process input
        if controller.process_input(player_input):
            prev_coins = len(game.coin_positions)

            # Check if a coin was collected this turn
            if prev_coins > len(game.coin_positions):
                print("Coin collected!")
                coins_collected += 1
                if not controller.manual_mode:
                    controller.chat_history.add_system_message("A coin was collected!")

            # Only advance turn if in manual mode or if we implement actual unit movement in chat mode
            if controller.manual_mode:
                game.next_turn()


if __name__ == "__main__":
    main()
