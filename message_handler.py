"""
Message handler module for the GPT Generals game.

This module provides a ChatMessage class and ChatHistory class to manage chat messages
for natural language interaction with units.
"""

from typing import List, Optional, Tuple, Union


class ChatMessage:
    """
    Class representing a chat message in the GPT Generals game.
    """

    def __init__(self, sender: str, content: str, sender_type: str = "player"):
        """
        Initialize a new chat message.

        Args:
            sender: The name of the sender
            content: The message content
            sender_type: The type of sender ("player", "unit", "system", "move")
        """
        self.sender = sender
        self.content = content
        self.sender_type = sender_type


class ChatHistory:
    """
    Class to store and manage chat messages in the GPT Generals game.
    """

    def __init__(self):
        """Initialize an empty chat history."""
        # Store messages as ChatMessage objects or (sender, content) tuples
        # for backward compatibility
        self.messages: List[Union[ChatMessage, Tuple[str, str]]] = []

        # Add a welcome message
        self.add_system_message("Welcome to GPT Generals! Type your commands to control units.")

    def add_message(self, message: ChatMessage) -> None:
        """
        Add a ChatMessage object to the chat history.

        Args:
            message: The ChatMessage object to add
        """
        self.messages.append(message)

    def add_player_message(self, content: str) -> None:
        """
        Add a message from the player to the chat history.

        Args:
            content: The message content
        """
        self.messages.append(ChatMessage("player", content, "player"))

    def add_unit_message(self, unit_name: str, content: str) -> None:
        """
        Add a message from a unit to the chat history.

        Args:
            unit_name: The name of the unit sending the message
            content: The message content
        """
        self.messages.append(ChatMessage(unit_name, content, "unit"))

    def add_system_message(self, content: str) -> None:
        """
        Add a system message to the chat history.

        Args:
            content: The message content
        """
        self.messages.append(ChatMessage("system", content, "system"))

    def add_move_message(self, content: str) -> None:
        """
        Add a movement message to the chat history.

        Args:
            content: The message content describing the movement
        """
        self.messages.append(ChatMessage("move", content, "move"))

    def get_last_n_messages(self, n: int) -> List[Union[ChatMessage, Tuple[str, str]]]:
        """
        Get the last n messages from the chat history.

        Args:
            n: Number of messages to retrieve

        Returns:
            List of ChatMessage objects or (sender, content) tuples
        """
        return self.messages[-n:] if n < len(self.messages) else self.messages[:]

    def get_all_messages(self) -> List[Union[ChatMessage, Tuple[str, str]]]:
        """
        Get all messages from the chat history.

        Returns:
            List of ChatMessage objects or (sender, content) tuples
        """
        return self.messages[:]

    def format_message(self, message: Union[ChatMessage, Tuple[str, str]]) -> str:
        """
        Format a message for display.

        Args:
            message: A ChatMessage object or (sender, content) tuple

        Returns:
            Formatted message string
        """
        if isinstance(message, ChatMessage):
            sender = message.sender
            content = message.content
        else:
            sender, content = message

        if sender == "system":
            return f"SYSTEM: {content}"
        elif sender == "player":
            return f"YOU: {content}"
        elif sender == "move":
            return f"MOVE: {content}"
        else:
            return f"UNIT {sender}: {content}"

    def format_chat_history(self, max_messages: Optional[int] = None) -> str:
        """
        Format the chat history for display.

        Args:
            max_messages: Maximum number of messages to include (from newest)

        Returns:
            Formatted chat history as a string
        """
        # Use all messages by default
        if max_messages is None:
            messages = self.messages
        else:
            # Only get the last max_messages
            messages = self.get_last_n_messages(max_messages)

        return "\n".join(self.format_message(msg) for msg in messages)
