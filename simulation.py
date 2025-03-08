import random

from game_engine import GameEngine


def run_simulation(num_turns: int = 10):
    """
    Run a simulation of the game with random unit movements for a specified number of turns.

    Args:
        num_turns: Number of turns to simulate (default 10)
    """
    game = GameEngine()

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
    run_simulation()
