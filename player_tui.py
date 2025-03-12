#!/usr/bin/env python3
"""
Text User Interface (TUI) for player-controlled GPT Generals game.

This module provides a terminal-based interface for playing the GPT Generals
game with real-time visualization and keyboard controls.
"""

import curses
import time
from typing import Optional

from game_engine import GameEngine
from player_controller import PlayerController


class PlayerTUI:
    """Terminal User Interface for interactive gameplay of GPT Generals."""

    def __init__(self, stdscr, game: GameEngine):
        """
        Initialize the TUI for player-controlled gameplay.

        Args:
            stdscr: The curses standard screen
            game: The game engine instance
        """
        self.stdscr = stdscr
        self.game = game
        self.controller = PlayerController(game)
        self.paused = False
        self.message: Optional[str] = None
        self.message_timeout = 0

        # Key mapping for unit selection and movement
        self.unit_keys = {ord(k.lower()): k for k in game.units.keys()}
        self.unit_keys.update({ord(k): k for k in game.units.keys()})

        self.direction_keys = {
            curses.KEY_UP: "w",  # Up arrow
            ord("w"): "w",  # W key (up)
            ord("W"): "w",  # W key (up)
            curses.KEY_DOWN: "s",  # Down arrow
            ord("s"): "s",  # S key (down)
            ord("S"): "s",  # S key (down)
            curses.KEY_LEFT: "a",  # Left arrow
            ord("a"): "a",  # A key (left)
            ord("A"): "a",  # A key (left)
            curses.KEY_RIGHT: "d",  # Right arrow
            ord("d"): "d",  # D key (right)
            ord("D"): "d",  # D key (right)
        }

        # Initialize colors
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLUE, -1)  # Water
        curses.init_pair(2, curses.COLOR_GREEN, -1)  # Land
        curses.init_pair(3, curses.COLOR_YELLOW, -1)  # Coins
        curses.init_pair(4, curses.COLOR_RED, -1)  # Unit A
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)  # Unit B
        curses.init_pair(6, curses.COLOR_WHITE, -1)  # Text
        curses.init_pair(7, curses.COLOR_GREEN, -1)  # Success messages
        curses.init_pair(8, curses.COLOR_RED, -1)  # Error messages

        # Clear screen and hide cursor
        self.stdscr.clear()
        curses.curs_set(0)

        # Get screen dimensions
        self.height, self.width = self.stdscr.getmaxyx()

        # Set up event handling
        self.stdscr.nodelay(True)  # Non-blocking input
        self.stdscr.timeout(100)  # Check for input every 100ms

        # Enable keypad mode (for arrow keys)
        self.stdscr.keypad(True)

        # Track active unit
        self.active_unit: Optional[str] = None

        # Total coins at start
        self.total_coins = len(game.coin_positions)

    def handle_input(self) -> bool:
        """
        Handle user input for game control.

        Returns:
            True if game should continue, False if it should exit
        """
        try:
            key = self.stdscr.getch()
            if key == ord("q") or key == ord("Q"):
                return False
            elif key == ord(" "):
                self.paused = not self.paused
            elif key == ord("h") or key == ord("H"):
                self.show_help()
            elif key in self.unit_keys:
                # Select a unit
                self.active_unit = self.unit_keys[key]
                self.message = f"Unit {self.active_unit} selected"
                self.message_timeout = time.time() + 2  # Show for 2 seconds
            elif self.active_unit and key in self.direction_keys:
                # Move the active unit
                direction_key = self.direction_keys[key]
                command = f"{self.active_unit}{direction_key}"
                success = self.controller.process_input(command)

                if success:
                    prev_coins = len(self.game.coin_positions)
                    # Check if a coin was collected
                    coins_collected = prev_coins > len(self.game.coin_positions)

                    if coins_collected:
                        self.message = f"Unit {self.active_unit} collected a coin!"
                    else:
                        dir_name = self.controller.direction_map[direction_key]
                        self.message = f"Unit {self.active_unit} moved {dir_name}"

                    # Advance turn
                    self.game.next_turn()
                else:
                    dir_name = self.controller.direction_map[direction_key]
                    self.message = f"Move failed. Unit {self.active_unit} cannot move {dir_name}."

                self.message_timeout = time.time() + 2  # Show for 2 seconds
        except Exception:
            pass

        return True

    def show_help(self):
        """Display help information."""
        self.message = "Controls: Select unit (A-Z), then move with arrow keys or WASD. Q to quit."
        self.message_timeout = time.time() + 5  # Show for 5 seconds

    def display_game(self):
        """Display the current game state."""
        self.stdscr.clear()

        # Display title
        title = f"GPT Generals - Turn {self.game.current_turn}"
        self.stdscr.addstr(0, (self.width - len(title)) // 2, title, curses.A_BOLD)

        # Display controls
        controls = "Controls: [q]uit | [space]pause/resume | [h]elp"
        coins_remaining = len(self.game.coin_positions)
        status = (
            f"Status: {'PAUSED' if self.paused else 'Running'} | "
            f"Coins: {coins_remaining}/{self.total_coins}"
        )

        # Only show if screen is wide enough
        if len(controls) < self.width:
            self.stdscr.addstr(1, 0, controls)
            self.stdscr.addstr(1, self.width - len(status) - 1, status)

        # Render the map
        map_lines = self.render_map().split("\n")

        start_y = 3
        for i, line in enumerate(map_lines):
            if start_y + i < self.height - 2:
                self.stdscr.addstr(start_y + i, 2, line)

        # Display unit positions and active unit
        unit_info = []
        for name, unit in self.game.units.items():
            if name == self.active_unit:
                unit_info.append(f"► Unit {name}: {unit.position} ◄")
            else:
                unit_info.append(f"Unit {name}: {unit.position}")

        unit_y = start_y + len(map_lines) + 1
        if unit_y < self.height - 1:
            self.stdscr.addstr(unit_y, 2, " | ".join(unit_info))

        # Display message if there is one
        if self.message and time.time() < self.message_timeout:
            message_y = self.height - 1
            self.stdscr.addstr(message_y, 2, self.message)

        self.stdscr.refresh()

    def render_map(self) -> str:
        """
        Create a string representation of the map.

        Returns:
            A string representation of the map
        """
        height = len(self.game.map_grid)
        width = len(self.game.map_grid[0]) if height > 0 else 0

        # Create the base map with terrain
        rows = []

        # Add header row with column numbers
        header = "  " + "".join(f"{i % 10}" for i in range(width))
        rows.append(header)

        # Render map grid
        for y in range(height):
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

    def run_game(self):
        """Run the main game loop with the TUI."""
        try:
            # Show initial state
            self.display_game()

            # Main game loop
            while True:
                # Check for win condition
                if not self.game.coin_positions:
                    turn_count = self.game.current_turn
                    self.message = (
                        f"Congratulations! You've collected all coins in {turn_count} turns."
                    )
                    self.message_timeout = time.time() + 10  # Show for 10 seconds
                    self.display_game()
                    time.sleep(3)  # Give time to see the message
                    break

                # Handle input for game control
                if not self.handle_input():
                    break

                # Check if paused
                if not self.paused:
                    # Update display
                    self.display_game()

                # Short delay for responsiveness without consuming too much CPU
                time.sleep(0.05)

            # Game over, show final state
            self.stdscr.clear()
            end_message = (
                "Game Over! All coins collected."
                if not self.game.coin_positions
                else "Game ended by player."
            )
            coins_remaining = len(self.game.coin_positions)
            coins_collected = self.total_coins - coins_remaining
            stats = (
                f"Turns played: {self.game.current_turn} | "
                f"Coins collected: {coins_collected}/{self.total_coins}"
            )

            mid_y = self.height // 2

            def center_x(text):
                return (self.width - len(text)) // 2

            self.stdscr.addstr(mid_y - 1, center_x(end_message), end_message, curses.A_BOLD)
            self.stdscr.addstr(mid_y + 1, center_x(stats), stats)
            self.stdscr.addstr(mid_y + 3, (self.width - 20) // 2, "Press any key to exit")

            self.stdscr.refresh()

            # Wait for a keypress before exiting
            self.stdscr.nodelay(False)
            self.stdscr.getch()

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            pass


def run_player_tui(game: GameEngine):
    """
    Run the player TUI with the provided game engine.

    Args:
        game: The game engine instance to use
    """
    curses.wrapper(lambda stdscr: PlayerTUI(stdscr, game).run_game())
