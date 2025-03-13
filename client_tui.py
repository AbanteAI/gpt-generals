#!/usr/bin/env python3
"""
Terminal User Interface client for GPT Generals game.

This module implements a TUI client that connects to the game server
and provides an interface for playing the game.
"""

import curses
import logging
import time
from typing import Optional

from game_client import GameClient, get_state_sync, move_unit_sync, reset_game_sync
from game_engine import GameEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class ClientTUI:
    """Terminal User Interface for the GPT Generals game client."""

    def __init__(self, stdscr, client: GameClient):
        """
        Initialize the TUI client.

        Args:
            stdscr: The curses standard screen
            client: GameClient instance already connected to the server
        """
        self.stdscr = stdscr
        self.client = client
        self.game: Optional[GameEngine] = None
        self.paused = False
        self.message: Optional[str] = None
        self.message_timeout = 0
        self.active_unit: Optional[str] = None
        self.total_coins = 0
        self.is_game_over = False

        # Initialize curses
        self._setup_curses()

        # Register callbacks for game state updates
        self._register_callbacks()

    def _setup_curses(self):
        """Initialize the curses environment."""
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

    def _register_callbacks(self):
        """Register callbacks for game state updates."""

        # Callback for when game state is updated
        def on_state_update(game):
            self.game = game
            if not hasattr(self, "total_coins") or self.total_coins == 0:
                self.total_coins = len(game.coin_positions) + 0  # Make a copy

            # Check for game over condition (all coins collected)
            if len(game.coin_positions) == 0:
                self.is_game_over = True
                self.message = f"Congratulations! All coins collected in {game.current_turn} turns."
                self.message_timeout = time.time() + 10  # Show for 10 seconds

        # Callback for move results
        def on_move_result(result):
            success = result.get("success", False)
            unit = result.get("unit_name", "Unknown")
            direction = result.get("direction", "Unknown")

            if success:
                # Check if the active unit is the one that moved
                if unit == self.active_unit:
                    self.message = f"Unit {unit} moved {direction}"
                else:
                    self.message = f"Unit {unit} (controlled by another client) moved {direction}"
            else:
                self.message = f"Move failed: {unit} couldn't move {direction}"

            self.message_timeout = time.time() + 2  # Show for 2 seconds

        # Callback for errors
        def on_error(error):
            self.message = f"Error: {error}"
            self.message_timeout = time.time() + 5  # Show error for 5 seconds

        # Register the callbacks
        self.client.register_state_update_callback(on_state_update)
        self.client.register_move_result_callback(on_move_result)
        self.client.register_error_callback(on_error)

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
            elif key == ord("r") or key == ord("R"):
                # Reset the game
                reset_game_sync(self.client)
                self.active_unit = None
                self.is_game_over = False
                self.message = "Game reset requested"
                self.message_timeout = time.time() + 2
            elif self.game:  # Only process game-specific inputs if we have a game state
                # Key mapping for unit selection
                unit_keys = {}
                for name in self.game.units.keys():
                    unit_keys[ord(name.lower())] = name
                    unit_keys[ord(name)] = name

                # Direction keys mapping
                direction_keys = {
                    curses.KEY_UP: "up",
                    ord("w"): "up",
                    ord("W"): "up",
                    curses.KEY_DOWN: "down",
                    ord("s"): "down",
                    ord("S"): "down",
                    curses.KEY_LEFT: "left",
                    ord("a"): "left",
                    ord("A"): "left",
                    curses.KEY_RIGHT: "right",
                    ord("d"): "right",
                    ord("D"): "right",
                }

                if key in unit_keys:
                    # Select a unit
                    self.active_unit = unit_keys[key]
                    self.message = f"Unit {self.active_unit} selected"
                    self.message_timeout = time.time() + 2  # Show for 2 seconds
                elif self.active_unit and key in direction_keys:
                    # Move the active unit
                    direction = direction_keys[key]
                    move_unit_sync(self.client, self.active_unit, direction)
                    # Note: The move result will be handled by the callback
        except Exception as e:
            logger.error(f"Error handling input: {e}")

        return True

    def show_help(self):
        """Display help information."""
        self.message = (
            "Controls: Select unit (A-Z), then move with arrow keys or WASD. R to reset. Q to quit."
        )
        self.message_timeout = time.time() + 5  # Show for 5 seconds

    def display_game(self):
        """Display the current game state."""
        self.stdscr.clear()

        if not self.game:
            # Display waiting message if we don't have a game state yet
            wait_msg = "Waiting for game state from server..."
            self.stdscr.addstr(self.height // 2, (self.width - len(wait_msg)) // 2, wait_msg)
            self.stdscr.refresh()
            return

        # Display title
        title = f"GPT Generals - Turn {self.game.current_turn}"
        self.stdscr.addstr(0, (self.width - len(title)) // 2, title, curses.A_BOLD)

        # Display controls
        controls = "Controls: [q]uit | [space]pause/resume | [h]elp | [r]eset"
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
        map_lines = self._render_map().split("\n")

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

        # Display connection status
        conn_status = "Connected to server" if self.client.connected else "Disconnected"
        conn_y = unit_y + 1
        if conn_y < self.height - 1:
            self.stdscr.addstr(
                conn_y,
                2,
                conn_status,
                curses.color_pair(7) if self.client.connected else curses.color_pair(8),
            )

        # Display message if there is one
        if self.message and time.time() < self.message_timeout:
            message_y = self.height - 1
            self.stdscr.addstr(message_y, 2, self.message)

        self.stdscr.refresh()

    def _render_map(self) -> str:
        """
        Create a string representation of the map.

        Returns:
            A string representation of the map
        """
        if not self.game:
            return "No map data available"

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
            # Request the initial game state
            get_state_sync(self.client)

            # Main game loop
            while True:
                # Display the current game state
                self.display_game()

                # Handle input for game control
                if not self.handle_input():
                    break

                # Check if game over and we should exit
                if self.is_game_over:
                    # Show game over for a bit then prompt to exit or restart
                    self.display_game()
                    time.sleep(3)  # Give time to see the message

                    # Ask if they want to restart or exit
                    self.stdscr.clear()
                    mid_y = self.height // 2
                    restart_msg = (
                        "Game over! All coins collected. Press 'r' to restart or 'q' to quit."
                    )
                    self.stdscr.addstr(mid_y, (self.width - len(restart_msg)) // 2, restart_msg)
                    self.stdscr.refresh()

                    # Wait for either 'r' or 'q'
                    self.stdscr.nodelay(False)  # Switch to blocking input
                    while True:
                        key = self.stdscr.getch()
                        if key == ord("q") or key == ord("Q"):
                            return  # Exit the game
                        elif key == ord("r") or key == ord("R"):
                            # Reset the game
                            reset_game_sync(self.client)
                            self.active_unit = None
                            self.is_game_over = False
                            self.stdscr.nodelay(True)  # Back to non-blocking
                            break  # Continue the game loop

                # Small delay for responsiveness
                time.sleep(0.05)

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            pass
        finally:
            # Ensure we disconnect from the server
            self.client.stop()


def run_client_tui(host: str = "localhost", port: int = 8765):
    """
    Run the TUI client connected to a server.

    Args:
        host: Server host address
        port: Server port
    """
    # Create and start the client
    client = GameClient(host=host, port=port)
    client.start()

    # Short delay to allow client to connect
    time.sleep(1)

    # Run the TUI with this client
    try:
        curses.wrapper(lambda stdscr: ClientTUI(stdscr, client).run_game())
    finally:
        # Make sure to stop the client
        client.stop()
        logger.info("Client stopped")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GPT Generals TUI Client")
    parser.add_argument("--host", default="localhost", help="Server host address")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Set log level
    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Run the TUI client
    run_client_tui(host=args.host, port=args.port)
