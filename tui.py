#!/usr/bin/env python3
"""
Text User Interface (TUI) for GPT Generals simulation.

This module provides a terminal-based interface to visualize the GPT Generals
game simulation with animated movements and delay between turns.
"""

import argparse
import curses
import random
import time
from typing import List

from game_engine import GameEngine
from simulation import get_unit_move_decision


class SimulationTUI:
    """Terminal User Interface for visualizing GPT Generals simulations."""

    def __init__(self, stdscr, game: GameEngine, delay: float = 0.5, use_llm: bool = False):
        """
        Initialize the TUI.

        Args:
            stdscr: The curses standard screen
            game: The game engine instance
            delay: Delay between turn updates in seconds
            use_llm: Whether to use LLM for movement decisions
        """
        self.stdscr = stdscr
        self.game = game
        self.delay = delay
        self.use_llm = use_llm
        self.paused = False
        self.directions = ["up", "down", "left", "right"]

        # Initialize colors
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLUE, -1)  # Water
        curses.init_pair(2, curses.COLOR_GREEN, -1)  # Land
        curses.init_pair(3, curses.COLOR_YELLOW, -1)  # Coins
        curses.init_pair(4, curses.COLOR_RED, -1)  # Unit A
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)  # Unit B
        curses.init_pair(6, curses.COLOR_WHITE, -1)  # Text

        # Clear screen and hide cursor
        self.stdscr.clear()
        curses.curs_set(0)

        # Get screen dimensions
        self.height, self.width = self.stdscr.getmaxyx()

        # Set up event handling
        self.stdscr.nodelay(True)  # Non-blocking input
        self.stdscr.timeout(100)  # Check for input every 100ms

    def handle_input(self) -> bool:
        """
        Handle user input.

        Returns:
            True if simulation should continue, False if it should exit
        """
        try:
            key = self.stdscr.getch()
            if key == ord("q"):
                return False
            elif key == ord(" "):
                self.paused = not self.paused
            elif key == ord("+") or key == ord("="):
                self.delay = max(0.1, self.delay - 0.1)
            elif key == ord("-"):
                self.delay += 0.1
        except Exception:
            pass
        return True

    def display_map(self, turn_number: int, messages: List[str]):
        """
        Display the current game map and stats.

        Args:
            turn_number: Current turn number
            messages: List of messages to display
        """
        self.stdscr.clear()

        # Display title and controls
        title = f"GPT Generals - Turn {turn_number}"
        self.stdscr.addstr(0, (self.width - len(title)) // 2, title, curses.A_BOLD)

        controls = "Controls: [q]uit | [space]pause/resume | [+/-]speed"
        status = f"Status: {'PAUSED' if self.paused else 'Running'} | Delay: {self.delay:.1f}s"

        # Only show if screen is wide enough
        if len(controls) < self.width:
            self.stdscr.addstr(1, 0, controls)
            self.stdscr.addstr(1, self.width - len(status) - 1, status)

        # Render the map
        map_lines = self.render_colored_map().split("\n")

        start_y = 3
        for i, line in enumerate(map_lines):
            if start_y + i < self.height - len(messages) - 1:
                self.stdscr.addstr(start_y + i, 2, line)

        # Show coin count and unit positions
        coin_count = f"Coins remaining: {len(self.game.coin_positions)}"
        self.stdscr.addstr(start_y + len(map_lines) + 1, 2, coin_count, curses.A_BOLD)

        # Display unit positions
        unit_positions = []
        for name, unit in self.game.units.items():
            unit_positions.append(f"Unit {name} at {unit.position}")

        self.stdscr.addstr(start_y + len(map_lines) + 2, 2, " | ".join(unit_positions))

        # Display messages
        message_y = self.height - len(messages) - 1
        for i, msg in enumerate(messages):
            if message_y + i < self.height:
                self.stdscr.addstr(message_y + i, 2, msg)

        self.stdscr.refresh()

    def render_colored_map(self) -> str:
        """
        Create a colored string representation of the map.

        Returns:
            A string representation of the map with curses color codes
        """
        height = len(self.game.map_grid)
        width = len(self.game.map_grid[0]) if height > 0 else 0

        # Create the base map with terrain
        rows = []

        # Add header row with column numbers
        header = "  " + "".join(f"{i % 10}" for i in range(width))
        rows.append(header)

        # Render map grid with colors in reverse order
        for y in range(height - 1, -1, -1):
            row = f"{y % 10} "
            for x in range(width):
                # Check for units and coins at this position
                char = None
                for name, unit in self.game.units.items():
                    if unit.position == (x, y):
                        char = name
                        break

                if char is None and (x, y) in self.game.coin_positions:
                    char = "c"

                if char is None:
                    char = self.game.map_grid[y][x].value

                row += char

            rows.append(row)

        return "\n".join(rows)

    def run_simulation(self, num_turns: int):
        """
        Run the simulation with visualization.

        Args:
            num_turns: Number of turns to simulate
        """
        try:
            # Show initial state
            self.display_map(0, ["Starting simulation..."])
            time.sleep(self.delay)

            for turn in range(1, num_turns + 1):
                messages = []

                # Handle input (allows quitting during delay)
                if not self.handle_input():
                    break

                # Check if paused
                while self.paused:
                    if not self.handle_input():
                        return
                    self.display_map(turn - 1, ["Simulation paused. Press SPACE to continue."])
                    time.sleep(0.1)

                messages.append(f"--- Turn {turn} ---")

                # Move each unit
                for unit_name in self.game.units:
                    if self.use_llm:
                        # Get move decision from LLM
                        messages.append(f"Consulting LLM for unit {unit_name}...")
                        self.display_map(turn, messages)

                        decision = get_unit_move_decision(self.game, unit_name)

                        if decision:
                            direction = decision.decision.direction
                            messages.append(
                                f"Unit {unit_name} reasoning: {decision.decision.reasoning}"
                            )
                        else:
                            direction = random.choice(self.directions)
                            messages.append(
                                f"LLM failed, Unit {unit_name} choosing random direction."
                            )
                    else:
                        # Use random movement
                        direction = random.choice(self.directions)

                    success = self.game.move_unit(unit_name, direction)
                    result = "Success" if success else "Failed"
                    messages.append(f"Unit {unit_name} attempts to move {direction}: {result}")

                    # Update display after each unit move to show animation
                    self.display_map(turn, messages)
                    time.sleep(self.delay / 2)  # Shorter delay for unit moves

                # Advance to next turn
                self.game.next_turn()

                # Update display for end of turn
                self.display_map(turn, messages + [f"\nEnd of Turn {turn}"])
                time.sleep(self.delay)

                # Allow quitting between turns
                if not self.handle_input():
                    break

            # Show final state
            self.display_map(num_turns, ["Simulation complete!", "Press 'q' to exit."])

            # Wait for user to quit
            while True:
                if not self.handle_input():
                    break
                time.sleep(0.1)

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            pass


def run_tui_simulation(
    num_turns: int = 10, use_custom_map: bool = False, use_llm: bool = False, delay: float = 0.5
):
    """
    Run a TUI-based simulation of the game.

    Args:
        num_turns: Number of turns to simulate
        use_custom_map: Whether to use a custom map
        use_llm: Whether to use LLM for movement decisions
        delay: Delay between turns in seconds
    """
    from game_engine import GameEngine
    from map_generator import MapGenerator

    # Create a game instance
    if use_custom_map:
        custom_map = MapGenerator.generate_random_map(width=15, height=10, water_probability=0.15)
        game = GameEngine(map_grid=custom_map, num_coins=8)
    else:
        game = GameEngine()

    # Run the curses application
    curses.wrapper(
        lambda stdscr: SimulationTUI(stdscr, game, delay, use_llm).run_simulation(num_turns)
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a GPT Generals TUI simulation.")
    parser.add_argument("--turns", type=int, default=10, help="Number of turns to simulate")
    parser.add_argument("--custom-map", action="store_true", help="Use a custom map")
    parser.add_argument("--llm", action="store_true", help="Use LLM for unit movement decisions")
    parser.add_argument(
        "--delay", type=float, default=0.5, help="Delay between turns in seconds (default: 0.5)"
    )

    args = parser.parse_args()

    run_tui_simulation(
        num_turns=args.turns, use_custom_map=args.custom_map, use_llm=args.llm, delay=args.delay
    )
