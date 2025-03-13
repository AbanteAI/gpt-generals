#!/usr/bin/env python3
"""
WebSocket client for GPT Generals game.

This module implements a client that connects to the game server
and provides an interface for controlling the game.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import Any, Callable, Dict, List, Optional

import websockets
from websockets.exceptions import ConnectionClosed

from game_engine import GameEngine, Unit
from map_generator import TerrainType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class GameClient:
    """WebSocket client for GPT Generals game."""

    def __init__(self, host: str = "localhost", port: int = 8765):
        """
        Initialize the game client.

        Args:
            host: Server host address
            port: Server port
        """
        self.host = host
        self.port = port
        self.websocket: Optional["websockets.WebSocketClientProtocol"] = None
        self.client_thread: Optional[threading.Thread] = None
        self.running = False
        self.connected = False

        # Initialize a local copy of the game state
        self.game = None

        # Callbacks for state updates and messages
        self.state_update_callbacks: List[Callable[[GameEngine], None]] = []
        self.move_result_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.error_callbacks: List[Callable[[str], None]] = []
        self.chat_message_callbacks: List[Callable[[Dict[str, Any]], None]] = []

    def register_state_update_callback(self, callback: Callable[[GameEngine], None]) -> None:
        """
        Register a callback to be called when game state is updated.

        Args:
            callback: Function that will be called with the updated game state
        """
        self.state_update_callbacks.append(callback)

    def register_move_result_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register a callback to be called when a move result is received.

        Args:
            callback: Function that will be called with the move result data
        """
        self.move_result_callbacks.append(callback)

    def register_error_callback(self, callback: Callable[[str], None]) -> None:
        """
        Register a callback to be called when an error occurs.

        Args:
            callback: Function that will be called with the error message
        """
        self.error_callbacks.append(callback)

    def register_chat_message_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register a callback to be called when a chat message is received.

        Args:
            callback: Function that will be called with the chat message data
        """
        self.chat_message_callbacks.append(callback)

    async def connect(self) -> bool:
        """
        Connect to the game server.

        Returns:
            True if connection was successful, False otherwise
        """
        logger.info(f"Connecting to server at ws://{self.host}:{self.port}")
        try:
            self.websocket = await websockets.connect(f"ws://{self.host}:{self.port}")
            self.connected = True
            logger.info("Connected to server")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from the game server."""
        if self.websocket and self.connected:
            await self.websocket.close()
            self.connected = False
            logger.info("Disconnected from server")

    def _deserialize_game_state(self, state_data: Dict[str, Any]) -> GameEngine:
        """
        Deserialize game state data received from the server.

        Args:
            state_data: Dictionary containing the game state

        Returns:
            GameEngine instance with the deserialized state
        """
        # Create a map grid from the serialized data
        map_grid = []
        for row in state_data["map_grid"]:
            map_grid_row = []
            for cell in row:
                map_grid_row.append(TerrainType.WATER if cell == "~" else TerrainType.LAND)
            map_grid.append(map_grid_row)

        # Create a game instance with the deserialized map
        game = GameEngine(map_grid=map_grid, num_coins=0)  # No coins initially

        # Override the turn counter
        game.current_turn = state_data["current_turn"]

        # Set the width and height
        game.width = state_data["width"]
        game.height = state_data["height"]

        # Clear and set players first (needed for units)
        game.players = {}
        if "players" in state_data:
            for player_id, player_data in state_data["players"].items():
                from game_engine import Player

                game.players[player_id] = Player(
                    id=player_data["id"], name=player_data["name"], color=player_data["color"]
                )

        # Clear and set units
        game.units = {}
        for name, unit_data in state_data["units"].items():
            # If the server provides a player_id, use it
            player_id = unit_data.get("player_id", "p0")
            game.units[name] = Unit(
                name=unit_data["name"], position=tuple(unit_data["position"]), player_id=player_id
            )

        # Set coin positions
        game.coin_positions = [tuple(pos) for pos in state_data["coin_positions"]]

        return game

    async def _process_message(self, message: str) -> None:
        """
        Process a message received from the server.

        Args:
            message: JSON string received from the server
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "game_state":
                # Update local game state
                self.game = self._deserialize_game_state(data)

                # Call state update callbacks
                for callback in self.state_update_callbacks:
                    try:
                        callback(self.game)
                    except Exception as e:
                        logger.error(f"Error in state update callback: {e}")

            elif message_type == "move_result":
                # Call move result callbacks
                for callback in self.move_result_callbacks:
                    try:
                        callback(data)
                    except Exception as e:
                        logger.error(f"Error in move result callback: {e}")

            elif message_type == "chat_message":
                # Log the chat message
                sender = data.get("sender", "unknown")
                content = data.get("content", "")
                sender_type = data.get("sender_type", "player")
                logger.info(f"Chat message from {sender} ({sender_type}): {content}")

                # Call chat message callbacks
                for callback in self.chat_message_callbacks:
                    try:
                        callback(data)
                    except Exception as e:
                        logger.error(f"Error in chat message callback: {e}")

            elif message_type == "error":
                error_message = data.get("message", "Unknown error")
                logger.error(f"Server error: {error_message}")

                # Call error callbacks
                for callback in self.error_callbacks:
                    try:
                        callback(error_message)
                    except Exception as e:
                        logger.error(f"Error in error callback: {e}")

            elif message_type == "reset_result":
                logger.info("Game has been reset")
                # Game state will be sent separately, no need to handle here

            else:
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            logger.error(f"Failed to parse message as JSON: {message}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def _receive_messages(self) -> None:
        """Receive and process messages from the server."""
        if not self.websocket:
            logger.error("Not connected to server")
            return

        try:
            async for message in self.websocket:
                await self._process_message(message)
        except ConnectionClosed:
            logger.info("Connection to server closed")
            self.connected = False
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
            self.connected = False

    async def _client_loop(self) -> None:
        """Main client loop for connecting and receiving messages."""
        try:
            while self.running:
                if not self.connected:
                    success = await self.connect()
                    if not success:
                        # Wait before retrying
                        await asyncio.sleep(5)
                        continue

                # Start receiving messages
                await self._receive_messages()

                # If we get here, the connection was closed
                # Wait before reconnecting
                if self.running:
                    logger.info("Attempting to reconnect...")
                    await asyncio.sleep(5)

        except asyncio.CancelledError:
            logger.info("Client loop cancelled")
        finally:
            # Ensure we're disconnected
            await self.disconnect()

    async def send_command(self, command: Dict[str, Any]) -> bool:
        """
        Send a command to the server.

        Args:
            command: Dictionary containing the command

        Returns:
            True if command was sent successfully, False otherwise
        """
        if not self.websocket or not self.connected:
            logger.error("Not connected to server")
            return False

        try:
            await self.websocket.send(json.dumps(command))
            return True
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            return False

    async def move_unit(
        self, unit_name: str, direction: str, player_id: Optional[str] = None
    ) -> bool:
        """
        Send a move command to the server.

        Args:
            unit_name: Name of the unit to move
            direction: Direction to move ('up', 'down', 'left', 'right')
            player_id: Optional player ID. If not provided, the server will verify ownership.

        Returns:
            True if command was sent successfully, False otherwise
        """
        command = {"command": "move", "unit_name": unit_name, "direction": direction}

        # Add player_id to the command if provided
        if player_id is not None:
            command["player_id"] = player_id

        return await self.send_command(command)

    async def send_chat_message(
        self, sender: str, content: str, sender_type: str = "player"
    ) -> bool:
        """
        Send a chat message to the server.

        Args:
            sender: Name of the sender (typically player name or id)
            content: Chat message content
            sender_type: Type of sender ("player", "unit", or "system")

        Returns:
            True if message was sent successfully, False otherwise
        """
        command = {
            "command": "chat",
            "sender": sender,
            "content": content,
            "sender_type": sender_type,
        }
        return await self.send_command(command)

    async def get_state(self) -> bool:
        """
        Request the current game state from the server.

        Returns:
            True if command was sent successfully, False otherwise
        """
        command = {"command": "get_state"}
        return await self.send_command(command)

    async def reset_game(self) -> bool:
        """
        Reset the game on the server.

        Returns:
            True if command was sent successfully, False otherwise
        """
        command = {"command": "reset"}
        return await self.send_command(command)

    def start(self) -> None:
        """Start the client in a separate thread."""
        if self.client_thread is not None and self.client_thread.is_alive():
            logger.warning("Client is already running")
            return

        self.running = True

        # Create a new event loop for the thread
        def run_client():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._client_loop())
            except Exception as e:
                logger.error(f"Error in client loop: {e}")
            finally:
                loop.close()

        # Start the client in a new thread
        self.client_thread = threading.Thread(target=run_client, daemon=True)
        self.client_thread.start()
        logger.info("Client started in background thread")

    def stop(self) -> None:
        """Stop the client."""
        if self.client_thread is None or not self.client_thread.is_alive():
            logger.warning("Client is not running")
            return

        # Set running to False
        self.running = False

        # Wait for the thread to exit
        if self.client_thread is not None:
            self.client_thread.join(timeout=5)
            if self.client_thread.is_alive():
                logger.warning("Client thread did not terminate gracefully")
            else:
                logger.info("Client stopped")
            self.client_thread = None


# Simple synchronous wrapper functions for easier use in synchronous code
def move_unit_sync(
    client: GameClient, unit_name: str, direction: str, player_id: Optional[str] = None
) -> bool:
    """
    Synchronous wrapper for move_unit.

    Args:
        client: GameClient instance
        unit_name: Name of the unit to move
        direction: Direction to move
        player_id: Optional player ID

    Returns:
        True if command was sent successfully, False otherwise
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(client.move_unit(unit_name, direction, player_id))
    finally:
        loop.close()


def get_state_sync(client: GameClient) -> bool:
    """
    Synchronous wrapper for get_state.

    Args:
        client: GameClient instance

    Returns:
        True if command was sent successfully, False otherwise
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(client.get_state())
    finally:
        loop.close()


def reset_game_sync(client: GameClient) -> bool:
    """
    Synchronous wrapper for reset_game.

    Args:
        client: GameClient instance

    Returns:
        True if command was sent successfully, False otherwise
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(client.reset_game())
    finally:
        loop.close()


def send_chat_message_sync(
    client: GameClient, sender: str, content: str, sender_type: str = "player"
) -> bool:
    """
    Synchronous wrapper for send_chat_message.

    Args:
        client: GameClient instance
        sender: Name of the sender (typically player name or id)
        content: Chat message content
        sender_type: Type of sender ("player", "unit", or "system")

    Returns:
        True if message was sent successfully, False otherwise
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(client.send_chat_message(sender, content, sender_type))
    finally:
        loop.close()


def main():
    """Run a simple test client."""
    import argparse
    import time

    parser = argparse.ArgumentParser(description="GPT Generals Game Client")
    parser.add_argument("--host", default="localhost", help="Server host address")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Set log level
    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Create and start the client
    client = GameClient(host=args.host, port=args.port)

    # Register callbacks
    def on_state_update(game):
        print("\nGame state updated:")
        print(game.render_map())
        print(f"Turn: {game.current_turn}")

        # Display units with positions
        units_str = ", ".join([f"{name} at {unit.position}" for name, unit in game.units.items()])
        print(f"Units: {units_str}")

        print(f"Coins: {len(game.coin_positions)}")

    def on_move_result(result):
        success = result.get("success", False)
        unit = result.get("unit_name", "Unknown")
        direction = result.get("direction", "Unknown")
        message = result.get("message", "")

        if success:
            print(f"Move successful: {unit} moved {direction}")
        else:
            print(f"Move failed: {unit} couldn't move {direction}. {message}")

    def on_error(error):
        print(f"Error: {error}")

    client.register_state_update_callback(on_state_update)
    client.register_move_result_callback(on_move_result)
    client.register_error_callback(on_error)

    # Start the client
    client.start()

    try:
        # Wait for connection
        print("Connecting to server...")
        time.sleep(2)

        # Request initial state
        get_state_sync(client)

        # Simple interactive loop
        while client.running and client.connected:
            command = (
                input("\nEnter command (move <unit> <direction>, state, reset, quit): ")
                .lower()
                .strip()
            )

            if command == "quit":
                break
            elif command == "state":
                get_state_sync(client)
            elif command == "reset":
                reset_game_sync(client)
            elif command.startswith("move "):
                parts = command.split()
                if len(parts) == 3:
                    _, unit, direction = parts
                    valid_directions = {"up", "down", "left", "right"}
                    if direction in valid_directions:
                        move_unit_sync(client, unit.upper(), direction)
                    else:
                        print(f"Invalid direction. Use one of: {', '.join(valid_directions)}")
                else:
                    print("Invalid move command. Format: move <unit> <direction>")
            else:
                print("Unknown command")

            # Short delay to allow for response
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Stop the client
        client.stop()


if __name__ == "__main__":
    main()
