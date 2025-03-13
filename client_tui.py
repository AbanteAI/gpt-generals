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

from game_client import (
    GameClient,
    get_state_sync,
    move_unit_sync,
    reset_game_sync,
    send_chat_message_sync,
)
from game_engine import GameEngine
from message_handler import ChatHistory, ChatMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class ChatInput:
    """A simple text input widget for chat messages."""

    def __init__(self, window, y: int, x: int, width: int):
        """
        Initialize the chat input widget.

        Args:
            window: The curses window to draw in
            y: Y position
            x: X position
            width: Width of the input field
        """
        self.window = window
        self.y = y
        self.x = x
        self.width = width
        self.buffer = ""
        self.cursor_pos = 0
        self.visible_start = 0

    def handle_key(self, key: int) -> Optional[str]:
        """
        Handle key input for the chat widget.

        Args:
            key: Key code from curses

        Returns:
            The submitted text if Enter was pressed, None otherwise
        """
        if key == curses.KEY_ENTER or key == 10 or key == 13:  # Enter
            result = self.buffer
            self.buffer = ""
            self.cursor_pos = 0
            self.visible_start = 0
            return result
        elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:  # Backspace
            if self.cursor_pos > 0:
                self.buffer = self.buffer[: self.cursor_pos - 1] + self.buffer[self.cursor_pos :]
                self.cursor_pos -= 1
                if self.visible_start > 0 and self.cursor_pos < self.visible_start:
                    self.visible_start -= 1
        elif key == curses.KEY_DC:  # Delete
            if self.cursor_pos < len(self.buffer):
                self.buffer = self.buffer[: self.cursor_pos] + self.buffer[self.cursor_pos + 1 :]
        elif key == curses.KEY_LEFT:  # Left arrow
            if self.cursor_pos > 0:
                self.cursor_pos -= 1
                if self.visible_start > 0 and self.cursor_pos < self.visible_start:
                    self.visible_start -= 1
        elif key == curses.KEY_RIGHT:  # Right arrow
            if self.cursor_pos < len(self.buffer):
                self.cursor_pos += 1
                if self.cursor_pos >= self.visible_start + self.width - 2:
                    self.visible_start += 1
        elif key == curses.KEY_HOME:  # Home
            self.cursor_pos = 0
            self.visible_start = 0
        elif key == curses.KEY_END:  # End
            self.cursor_pos = len(self.buffer)
            if self.cursor_pos >= self.width - 2:
                self.visible_start = self.cursor_pos - (self.width - 3)
        elif 32 <= key <= 126:  # Printable ASCII characters
            self.buffer = self.buffer[: self.cursor_pos] + chr(key) + self.buffer[self.cursor_pos :]
            self.cursor_pos += 1
            if self.cursor_pos >= self.visible_start + self.width - 2:
                self.visible_start += 1

        return None

    def draw(self):
        """Draw the input field with current text and cursor."""
        # Calculate visible portion of text
        visible_text = self.buffer[self.visible_start : self.visible_start + self.width - 2]

        # Draw input field border and content
        self.window.addstr(self.y, self.x, "┌" + "─" * (self.width - 2) + "┐")
        self.window.addstr(self.y + 1, self.x, "│" + " " * (self.width - 2) + "│")
        self.window.addstr(self.y + 2, self.x, "└" + "─" * (self.width - 2) + "┘")

        # Show the buffer text
        if visible_text:
            self.window.addstr(self.y + 1, self.x + 1, visible_text)

        # Set cursor position
        cursor_x = self.x + 1 + (self.cursor_pos - self.visible_start)
        self.window.move(self.y + 1, cursor_x)


class ClientTUI:
    """Terminal User Interface for the GPT Generals game client."""

    def __init__(self, stdscr, client: GameClient, manual_mode: bool = False):
        """
        Initialize the TUI client.

        Args:
            stdscr: The curses standard screen
            client: GameClient instance already connected to the server
            manual_mode: Whether to start in manual control mode (default False)
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
        self.manual_mode = manual_mode
        self.chat_history = ChatHistory()
        self.chat_input: Optional[ChatInput] = None
        self.chat_mode_active = False
        self.player_name = "Player"  # Default player name

        # Initialize curses
        self._setup_curses()

        # Register callbacks for game state updates and chat messages
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
        """Register callbacks for game state updates and chat messages."""

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

        # Callback for chat messages
        def on_chat_message(data):
            sender = data.get("sender", "Unknown")
            content = data.get("content", "")
            sender_type = data.get("sender_type", "player")

            # Create a ChatMessage and add it to our history
            message = ChatMessage(sender, content, sender_type)
            self.chat_history.add_message(message)

            # Set a temporary message notification
            if sender != self.player_name:  # Don't notify about our own messages
                self.message = (
                    f"New message from {sender}: {content[:20]}..."
                    if len(content) > 20
                    else f"New message from {sender}: {content}"
                )
                self.message_timeout = time.time() + 2  # Show for 2 seconds

        # Callback for errors
        def on_error(error):
            self.message = f"Error: {error}"
            self.message_timeout = time.time() + 5  # Show error for 5 seconds

        # Register the callbacks
        self.client.register_state_update_callback(on_state_update)
        self.client.register_move_result_callback(on_move_result)
        self.client.register_chat_message_callback(on_chat_message)
        self.client.register_error_callback(on_error)

    def handle_input(self) -> bool:
        """
        Handle user input for game control.

        Returns:
            True if game should continue, False if it should exit
        """
        try:
            # If we're in chat input mode, handle differently
            if self.chat_mode_active and not self.manual_mode:
                return self.handle_chat_input()

            key = self.stdscr.getch()
            if key == -1:  # No input
                return True

            if key == ord("q") or key == ord("Q"):
                return False
            elif key == ord(" "):
                self.paused = not self.paused
            elif key == ord("h") or key == ord("H"):
                self.show_help()
            elif key == ord("t") or key == ord("T"):
                # Toggle between manual and chat modes
                self.manual_mode = not self.manual_mode
                mode_name = "manual" if self.manual_mode else "chat"
                self.message = f"Switched to {mode_name} mode"
                self.message_timeout = time.time() + 2
            elif key == ord("c") or key == ord("C"):
                # Enter chat input mode if we're in chat mode
                if not self.manual_mode:
                    self.start_chat_input()
                    return True
            elif key == ord("r") or key == ord("R"):
                # Reset the game
                reset_game_sync(self.client)
                self.active_unit = None
                self.is_game_over = False
                self.message = "Game reset requested"
                self.message_timeout = time.time() + 2
            elif self.game and self.manual_mode:  # Only process game-specific inputs in manual mode
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

    def handle_chat_input(self) -> bool:
        """
        Handle input when in chat input mode.

        Returns:
            True if game should continue, False if it should exit
        """
        try:
            key = self.stdscr.getch()
            if key == -1:  # No input
                return True

            if key == 27:  # Escape - exit chat mode
                self.exit_chat_input()
                return True

            # Let chat input handle the key
            if self.chat_input:
                message = self.chat_input.handle_key(key)
                if message is not None and message.strip():
                    # Send the message
                    send_chat_message_sync(self.client, self.player_name, message, "player")
                    self.exit_chat_input()

                # Redraw input field
                self.chat_input.draw()

            # Make cursor visible in chat mode
            curses.curs_set(1)

        except Exception as e:
            logger.error(f"Error handling chat input: {e}")

        return True

    def start_chat_input(self):
        """Enter chat input mode."""
        self.chat_mode_active = True
        input_width = self.width - 4  # Leave some margin
        input_y = self.height - 4

        # Create chat input at the bottom of the screen
        self.chat_input = ChatInput(self.stdscr, input_y, 2, input_width)
        self.chat_input.draw()

        # Make cursor visible
        curses.curs_set(1)

    def exit_chat_input(self):
        """Exit chat input mode."""
        self.chat_mode_active = False
        curses.curs_set(0)  # Hide cursor

    def show_help(self):
        """Display help information."""
        if self.manual_mode:
            self.message = (
                "Manual Mode: Select unit, use arrows/WASD. T: toggle mode. Q: quit. R: reset."
            )
        else:
            self.message = (
                "Chat Mode: Press C to enter a message. T: toggle mode. Q: quit. R: reset."
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
        mode_name = "MANUAL" if self.manual_mode else "CHAT"
        controls = f"[q]uit | [t]oggle mode ({mode_name}) | [h]elp | [r]eset"
        coins_remaining = len(self.game.coin_positions)
        status = (
            f"Status: {'PAUSED' if self.paused else 'Running'} | "
            f"Coins: {coins_remaining}/{self.total_coins}"
        )

        # Only show if screen is wide enough
        if len(controls) < self.width:
            self.stdscr.addstr(1, 0, controls)
            self.stdscr.addstr(1, self.width - len(status) - 1, status)

        # Determine if we show chat pane
        show_chat = not self.manual_mode and self.width >= 80

        # Calculate map display area
        map_width = (self.width // 2) - 2 if show_chat else self.width - 4

        # Render the map with limited width
        map_lines = self._render_map(max_width=map_width).split("\n")

        # Display map
        start_y = 3
        for i, line in enumerate(map_lines):
            if start_y + i < self.height - 5:  # Leave room for status and input
                self.stdscr.addstr(start_y + i, 2, line)

        # Display unit positions and active unit
        unit_info = []
        for name, unit in self.game.units.items():
            if name == self.active_unit and self.manual_mode:
                unit_info.append(f"► Unit {name}: {unit.position} ◄")
            else:
                unit_info.append(f"Unit {name}: {unit.position}")

        unit_text = " | ".join(unit_info)
        if len(unit_text) > map_width:
            unit_text = unit_text[: map_width - 3] + "..."

        unit_y = start_y + len(map_lines) + 1
        if unit_y < self.height - 4:
            self.stdscr.addstr(unit_y, 2, unit_text)

        # Display connection status
        conn_status = "Connected to server" if self.client.connected else "Disconnected"
        conn_y = unit_y + 1
        if conn_y < self.height - 3:
            self.stdscr.addstr(
                conn_y,
                2,
                conn_status,
                curses.color_pair(7) if self.client.connected else curses.color_pair(8),
            )

        # Display chat history in chat mode
        if show_chat:
            chat_x = map_width + 4
            chat_width = self.width - chat_x - 2
            self.display_chat(start_y, chat_x, chat_width)

        # Display message if there is one
        if self.message and time.time() < self.message_timeout:
            message_y = self.height - 2 if not self.chat_mode_active else self.height - 6
            self.stdscr.addstr(message_y, 2, self.message)

        # If in chat input mode, draw the input field
        if self.chat_mode_active and self.chat_input:
            self.chat_input.draw()

        self.stdscr.refresh()

    def display_chat(self, start_y: int, x: int, width: int):
        """
        Display the chat history in a separate pane.

        Args:
            start_y: Starting Y position for chat display
            x: X position for chat display
            width: Width of chat display area
        """
        # Draw chat panel border
        title = " Chat History "
        border_top = f"┌{title:─^{width - 2}}┐"
        self.stdscr.addstr(start_y, x, border_top)

        # Draw side borders
        for i in range(1, self.height - start_y - 5):
            self.stdscr.addstr(start_y + i, x, "│")
            self.stdscr.addstr(start_y + i, x + width - 1, "│")

        # Draw bottom border
        self.stdscr.addstr(self.height - 5, x, f"└{'─' * (width - 2)}┘")

        # Display chat messages
        chat_history = self.chat_history.format_chat_history(max_messages=10)
        messages = chat_history.split("\n")

        # Calculate available height for messages
        available_height = self.height - start_y - 6
        display_messages = (
            messages[-available_height:] if len(messages) > available_height else messages
        )

        for i, msg in enumerate(display_messages):
            if start_y + i + 1 < self.height - 5:
                # Truncate message if needed
                if len(msg) > width - 4:
                    msg = msg[: width - 7] + "..."

                # Color different types of messages
                msg_color = curses.color_pair(6)  # Default color
                if msg.startswith("SYSTEM:"):
                    msg_color = curses.color_pair(8)
                elif msg.startswith(f"{self.player_name}:"):
                    msg_color = curses.color_pair(7)
                else:
                    msg_color = curses.color_pair(9)

                self.stdscr.addstr(start_y + i + 1, x + 1, msg, msg_color)

    def _render_map(self, max_width: Optional[int] = None) -> str:
        """
        Create a string representation of the map.

        Args:
            max_width: Optional maximum width for the map

        Returns:
            A string representation of the map
        """
        if not self.game:
            return "No map data available"

        height = len(self.game.map_grid)
        width = len(self.game.map_grid[0]) if height > 0 else 0

        # Limit width if specified
        if max_width is not None and max_width < width + 3:  # +3 for row numbers and spacing
            visible_width = max_width - 3
        else:
            visible_width = width

        # Create the base map with terrain
        rows = []

        # Add header row with column numbers
        header = "  " + "".join(f"{i % 10}" for i in range(visible_width))
        rows.append(header)

        # Render map grid
        for y in range(height):
            row = f"{y % 10} "
            for x in range(visible_width):
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


def run_client_tui(host: str = "localhost", port: int = 8765, manual_mode: bool = False):
    """
    Run the TUI client connected to a server.

    Args:
        host: Server host address
        port: Server port
        manual_mode: Whether to start in manual control mode (default False)
    """
    # Create and start the client
    client = GameClient(host=host, port=port)
    client.start()

    # Short delay to allow client to connect
    time.sleep(1)

    # Run the TUI with this client
    try:
        curses.wrapper(lambda stdscr: ClientTUI(stdscr, client, manual_mode).run_game())
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
