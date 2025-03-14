"""
Player controller module for the GPT Generals game.
"""

from typing import Optional

from message_handler import ChatHistory


class PlayerController:
    """
    Controller class for human player input in the GPT Generals game.
    """

    def __init__(self, game_engine, manual_mode=False):
        """
        Initialize the player controller.

        Args:
            game_engine: GameEngine instance to control
            manual_mode: If True, use manual control mode with unit/direction commands
                        If False, use natural language input mode (default)
        """
        self.game_engine = game_engine
        self.manual_mode = manual_mode
        self.chat_history = ChatHistory()
        self.direction_map = {
            "w": "up",
            "a": "left",
            "s": "down",
            "d": "right",
            "k": "up",  # vim-style up
            "h": "left",  # vim-style left
            "j": "down",  # vim-style down
            "l": "right",  # vim-style right
        }

    def process_input(self, player_input: str) -> bool:
        """
        Process player input and apply it to the game.

        Args:
            player_input: Either a manual control command "<unit_letter><direction>"
                          or a natural language command, depending on mode

        Returns:
            True if the input was valid and any action was successful, False otherwise
        """
        # Check if we're in manual mode
        if self.manual_mode:
            return self._process_manual_input(player_input)
        else:
            return self._process_natural_language(player_input)

    def _process_manual_input(self, player_input: str) -> bool:
        """
        Process manual mode input with unit/direction format.

        Args:
            player_input: Input string in the format "<unit_letter><direction>"
                          e.g., "Aw" to move unit A up

        Returns:
            True if the input was valid and the move was successful, False otherwise
        """
        # Validate input format
        if len(player_input) != 2:
            print("Invalid input. Please use format: <unit_letter><direction>")
            return False

        unit_name = player_input[0].upper()
        direction_key = player_input[1].lower()

        # Check if unit exists
        if unit_name not in self.game_engine.units:
            units_list = list(self.game_engine.units.keys())
            print(f"Unit '{unit_name}' not found. Available units: {units_list}")
            return False

        # Check if direction is valid
        if direction_key not in self.direction_map:
            print("Invalid direction. Please use w/k (up), a/h (left), s/j (down), d/l (right)")
            return False

        # Translate wasd to game directions
        direction = self.direction_map[direction_key]

        # Get the player's ID from the game engine based on the unit name
        unit = self.game_engine.units.get(unit_name)
        if unit:
            # Check if the unit exists in the game
            player_id = unit.player_id
        else:
            player_id = None

        # Try to move the unit
        success = self.game_engine.move_unit(unit_name, direction, player_id)

        if success:
            # Add a movement message to chat history
            self.chat_history.add_move_message(f"{unit_name} moved {direction}")
        else:
            print(f"Move failed. Unit {unit_name} cannot move {direction}.")

        return success

    def _process_natural_language(self, player_input: str) -> bool:
        """
        Process natural language input.

        Args:
            player_input: A natural language command

        Returns:
            True if the input was processed successfully, False otherwise
        """
        # Add the player's message to chat history
        self.chat_history.add_player_message(player_input)

        # For now, just acknowledge the input without doing anything
        # Later this would be processed by an LLM to determine what actions to take
        message = (
            f"Received your message: '{player_input}'. "
            f"Natural language processing not implemented yet."
        )
        self.chat_history.add_system_message(message)

        # Always return True since we're just adding to chat history
        return True

    def toggle_mode(self):
        """Toggle between manual and natural language input modes."""
        self.manual_mode = not self.manual_mode
        mode_name = "manual" if self.manual_mode else "natural language"
        message = f"Switched to {mode_name} input mode."
        self.chat_history.add_system_message(message)
        print(message)

    def get_chat_history(self, max_messages: Optional[int] = None):
        """
        Get formatted chat history.

        Args:
            max_messages: Maximum number of messages to include

        Returns:
            Formatted chat history as a string
        """
        return self.chat_history.format_chat_history(max_messages)
