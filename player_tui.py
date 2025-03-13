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


class PlayerTUI:
    """Terminal User Interface for interactive gameplay of GPT Generals."""

    def __init__(self, stdscr, game: GameEngine, manual_mode: bool = False):
        """
        Initialize the TUI for player-controlled gameplay.

        Args:
            stdscr: The curses standard screen
            game: The game engine instance
            manual_mode: Whether to start in manual control mode (default False)
        """
        self.stdscr = stdscr
        self.game = game
        self.controller = PlayerController(game, manual_mode=manual_mode)
        self.paused = False
        self.message: Optional[str] = None
        self.message_timeout = 0
        self.chat_input: Optional[ChatInput] = None
        self.chat_mode_active = False  # Flag to track if we're in chat input mode

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
        curses.init_pair(9, curses.COLOR_CYAN, -1)  # Chat messages

        # Clear screen and set up cursor visibility
        self.stdscr.clear()
        curses.curs_set(0)  # Hide cursor initially

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
            # If we're in chat input mode, handle differently
            if self.chat_mode_active and not self.controller.manual_mode:
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
                self.controller.toggle_mode()
                mode_name = "manual" if self.controller.manual_mode else "chat"
                self.message = f"Switched to {mode_name} mode"
                self.message_timeout = time.time() + 2
            elif key == ord("c") or key == ord("C"):
                # Enter chat input mode if we're in chat mode
                if not self.controller.manual_mode:
                    self.start_chat_input()
                    return True
            elif self.controller.manual_mode and key in self.unit_keys:
                # Manual mode: Select a unit
                self.active_unit = self.unit_keys[key]
                self.message = f"Unit {self.active_unit} selected"
                self.message_timeout = time.time() + 2  # Show for 2 seconds
            elif self.controller.manual_mode and self.active_unit and key in self.direction_keys:
                # Manual mode: Move the active unit
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
                    # Process the message
                    self.controller.process_input(message)
                    self.exit_chat_input()

                # Redraw input field
                self.chat_input.draw()

            # Make cursor visible in chat mode
            curses.curs_set(1)

        except Exception:
            pass

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
        if self.controller.manual_mode:
            self.message = "Manual Mode: Select unit (A-Z), then use arrows/WASD. T to toggle mode. Q to quit."
        else:
            self.message = "Chat Mode: Press 'c' to enter a message. T to toggle mode. Q to quit."
        self.message_timeout = time.time() + 5  # Show for 5 seconds

    def display_game(self):
        """Display the current game state."""
        self.stdscr.clear()

        # Display title
        title = f"GPT Generals - Turn {self.game.current_turn}"
        self.stdscr.addstr(0, (self.width - len(title)) // 2, title, curses.A_BOLD)

        # Display controls
        mode_name = "MANUAL" if self.controller.manual_mode else "CHAT"
        controls = f"[q]uit | [t]oggle mode ({mode_name}) | [h]elp"
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
        show_chat = not self.controller.manual_mode and self.width >= 80

        # Calculate map display area
        map_width = (self.width // 2) - 2 if show_chat else self.width - 4

        # Render the map with limited width
        map_lines = self.render_map(max_width=map_width).split("\n")

        # Display map
        start_y = 3
        for i, line in enumerate(map_lines):
            if start_y + i < self.height - 5:  # Leave room for status and input
                self.stdscr.addstr(start_y + i, 2, line)

        # Display unit positions and active unit
        unit_info = []
        for name, unit in self.game.units.items():
            if name == self.active_unit and self.controller.manual_mode:
                unit_info.append(f"► Unit {name}: {unit.position} ◄")
            else:
                unit_info.append(f"Unit {name}: {unit.position}")

        unit_text = " | ".join(unit_info)
        if len(unit_text) > map_width:
            unit_text = unit_text[: map_width - 3] + "..."

        unit_y = start_y + len(map_lines) + 1
        if unit_y < self.height - 4:
            self.stdscr.addstr(unit_y, 2, unit_text)

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
        chat_history = self.controller.get_chat_history(max_messages=10)
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
                elif msg.startswith("YOU:"):
                    msg_color = curses.color_pair(7)
                elif msg.startswith("UNIT"):
                    msg_color = curses.color_pair(9)

                self.stdscr.addstr(start_y + i + 1, x + 1, msg, msg_color)

    def render_map(self, max_width: Optional[int] = None) -> str:
        """
        Create a string representation of the map.

        Args:
            max_width: Optional maximum width for the map

        Returns:
            A string representation of the map
        """
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


def run_player_tui(game: GameEngine, manual_mode: bool = False):
    """
    Run the player TUI with the provided game engine.

    Args:
        game: The game engine instance to use
        manual_mode: Whether to start in manual control mode (default False)
    """
    curses.wrapper(lambda stdscr: PlayerTUI(stdscr, game, manual_mode).run_game())
