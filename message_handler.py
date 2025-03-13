"""
Message handler module for the GPT Generals game.

This module provides a ChatHistory class to manage chat messages
for natural language interaction with units.
"""

from typing import List, Tuple


class ChatHistory:
    """
    Class to store and manage chat messages in the GPT Generals game.
    """

    def __init__(self):
        """Initialize an empty chat history."""
        # Store messages as tuples of (sender, content)
        # sender can be a unit name, "player", or "system"
        self.messages: List[Tuple[str, str]] = []

        # Add a welcome message
        self.add_system_message("Welcome to GPT Generals! Type your commands to control units.")

    def add_player_message(self, content: str) -> None:
        """
        Add a message from the player to the chat history.

        Args:
            content: The message content
        """
        self.messages.append(("player", content))

    def add_unit_message(self, unit_name: str, content: str) -> None:
        """
        Add a message from a unit to the chat history.

        Args:
            unit_name: The name of the unit sending the message
            content: The message content
        """
        self.messages.append((unit_name, content))

    def add_system_message(self, content: str) -> None:
        """
        Add a system message to the chat history.

        Args:
            content: The message content
        """
        self.messages.append(("system", content))

    def get_last_n_messages(self, n: int) -> List[Tuple[str, str]]:
        """
        Get the last n messages from the chat history.

        Args:
            n: Number of messages to retrieve

        Returns:
            List of (sender, content) tuples
        """
        return self.messages[-n:] if n < len(self.messages) else self.messages[:]

    def get_all_messages(self) -> List[Tuple[str, str]]:
        """
        Get all messages from the chat history.

        Returns:
            List of (sender, content) tuples
        """
        return self.messages[:]

    def format_message(self, message: Tuple[str, str]) -> str:
        """
        Format a message for display.

        Args:
            message: A (sender, content) tuple

        Returns:
            Formatted message string
        """
        sender, content = message

        if sender == "system":
            return f"SYSTEM: {content}"
        elif sender == "player":
            return f"YOU: {content}"
        else:
            return f"UNIT {sender}: {content}"

    def format_chat_history(self, max_messages: int = None) -> str:
        """
        Format the chat history for display.

        Args:
            max_messages: Maximum number of messages to include (from newest)

        Returns:
            Formatted chat history as a string
        """
        messages = self.messages
        if max_messages is not None:
            messages = self.get_last_n_messages(max_messages)

        return "\n".join(self.format_message(msg) for msg in messages)
