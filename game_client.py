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

        # Lobby state
        self.lobby_state = {"rooms": []}
        self.current_room_id = None
        self.player_name = f"Player_{id(self)}"
        self.player_color = "#F44336"  # Default red

        # Callbacks for state updates and messages
        self.state_update_callbacks: List[Callable[[GameEngine], None]] = []
        self.move_result_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.error_callbacks: List[Callable[[str], None]] = []
        self.chat_message_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.lobby_state_callbacks: List[Callable[[Dict[str, Any]], None]] = []

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

    def register_lobby_state_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register a callback to be called when lobby state is updated.

        Args:
            callback: Function that will be called with the lobby state data
        """
        self.lobby_state_callbacks.append(callback)

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
                # Handle both WATER/LAND strings and ~/. symbols
                if cell == "~" or cell == "WATER":
                    map_grid_row.append(TerrainType.WATER)
                else:
                    map_grid_row.append(TerrainType.LAND)
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

            elif message_type == "lobby_state":
                # Update local lobby state
                self.lobby_state = data

                # Log the lobby state
                rooms = data.get("rooms", [])
                logger.info(f"Received lobby state with {len(rooms)} room(s)")

                # Call lobby state callbacks
                for callback in self.lobby_state_callbacks:
                    try:
                        callback(data)
                    except Exception as e:
                        logger.error(f"Error in lobby state callback: {e}")

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

            elif message_type == "room_created":
                success = data.get("success", False)
                room_id = data.get("room_id", "")
                room_name = data.get("room_name", "")

                if success:
                    logger.info(f"Room created: {room_name} (ID: {room_id})")
                    self.current_room_id = room_id
                else:
                    logger.error(f"Failed to create room: {data.get('message', 'Unknown error')}")

            elif message_type == "room_joined":
                success = data.get("success", False)
                room_id = data.get("room_id", "")
                room_name = data.get("room_name", "")

                if success:
                    logger.info(f"Joined room: {room_name} (ID: {room_id})")
                    self.current_room_id = room_id
                else:
                    logger.error(f"Failed to join room: {data.get('message', 'Unknown error')}")

            elif message_type == "room_left":
                success = data.get("success", False)

                if success:
                    logger.info("Left room")
                    self.current_room_id = None
                else:
                    logger.error(f"Failed to leave room: {data.get('message', 'Unknown error')}")

            elif message_type == "game_started":
                success = data.get("success", False)
                room_id = data.get("room_id", "")

                if success:
                    logger.info(f"Game started in room {room_id}")
                else:
                    logger.error(f"Failed to start game: {data.get('message', 'Unknown error')}")

            elif message_type == "player_info_updated":
                success = data.get("success", False)

                if success:
                    logger.info("Player info updated")
                else:
                    logger.error(
                        f"Failed to update player info: {data.get('message', 'Unknown error')}"
                    )

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

    async def get_lobby_state(self) -> bool:
        """
        Request the current lobby state from the server.

        Returns:
            True if command was sent successfully, False otherwise
        """
        command = {"command": "get_lobby_state"}
        return await self.send_command(command)

    async def create_room(
        self, room_name: str, player_name: str, player_color: str = "#F44336"
    ) -> bool:
        """
        Create a new game room.

        Args:
            room_name: Name of the room to create
            player_name: Name of the player creating the room
            player_color: Color of the player (hex format)

        Returns:
            True if command was sent successfully, False otherwise
        """
        self.player_name = player_name
        self.player_color = player_color

        command = {
            "command": "lobby_create_room",
            "room_name": room_name,
            "player_name": player_name,
            "player_color": player_color,
        }
        return await self.send_command(command)

    async def join_room(
        self, room_id: str, player_name: str, player_color: str = "#2196F3"
    ) -> bool:
        """
        Join an existing game room.

        Args:
            room_id: ID of the room to join
            player_name: Name of the player joining the room
            player_color: Color of the player (hex format)

        Returns:
            True if command was sent successfully, False otherwise
        """
        self.player_name = player_name
        self.player_color = player_color

        command = {
            "command": "lobby_join_room",
            "room_id": room_id,
            "player_name": player_name,
            "player_color": player_color,
        }
        return await self.send_command(command)

    async def leave_room(self) -> bool:
        """
        Leave the current game room.

        Returns:
            True if command was sent successfully, False otherwise
        """
        command = {"command": "lobby_leave_room"}
        return await self.send_command(command)

    async def start_game(self) -> bool:
        """
        Start the game in the current room (host only).

        Returns:
            True if command was sent successfully, False otherwise
        """
        command = {"command": "lobby_start_game"}
        return await self.send_command(command)

    async def set_player_info(self, player_name: str, player_color: str) -> bool:
        """
        Update player information.

        Args:
            player_name: New player name
            player_color: New player color (hex format)

        Returns:
            True if command was sent successfully, False otherwise
        """
        self.player_name = player_name
        self.player_color = player_color

        command = {
            "command": "lobby_set_player_info",
            "player_name": player_name,
            "player_color": player_color,
        }
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


# Synchronous wrapper functions for lobby commands
def get_lobby_state_sync(client: GameClient) -> bool:
    """
    Synchronous wrapper for get_lobby_state.

    Args:
        client: GameClient instance

    Returns:
        True if command was sent successfully, False otherwise
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(client.get_lobby_state())
    finally:
        loop.close()


def create_room_sync(
    client: GameClient, room_name: str, player_name: str, player_color: str = "#F44336"
) -> bool:
    """
    Synchronous wrapper for create_room.

    Args:
        client: GameClient instance
        room_name: Name of the room to create
        player_name: Name of the player creating the room
        player_color: Color of the player (hex format)

    Returns:
        True if command was sent successfully, False otherwise
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(client.create_room(room_name, player_name, player_color))
    finally:
        loop.close()


def join_room_sync(
    client: GameClient, room_id: str, player_name: str, player_color: str = "#2196F3"
) -> bool:
    """
    Synchronous wrapper for join_room.

    Args:
        client: GameClient instance
        room_id: ID of the room to join
        player_name: Name of the player joining the room
        player_color: Color of the player (hex format)

    Returns:
        True if command was sent successfully, False otherwise
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(client.join_room(room_id, player_name, player_color))
    finally:
        loop.close()


def leave_room_sync(client: GameClient) -> bool:
    """
    Synchronous wrapper for leave_room.

    Args:
        client: GameClient instance

    Returns:
        True if command was sent successfully, False otherwise
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(client.leave_room())
    finally:
        loop.close()


def start_game_sync(client: GameClient) -> bool:
    """
    Synchronous wrapper for start_game.

    Args:
        client: GameClient instance

    Returns:
        True if command was sent successfully, False otherwise
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(client.start_game())
    finally:
        loop.close()


def set_player_info_sync(client: GameClient, player_name: str, player_color: str) -> bool:
    """
    Synchronous wrapper for set_player_info.

    Args:
        client: GameClient instance
        player_name: New player name
        player_color: New player color (hex format)

    Returns:
        True if command was sent successfully, False otherwise
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(client.set_player_info(player_name, player_color))
    finally:
        loop.close()


def main():
    """Run a simple test client."""
    import argparse
    import random
    import time

    parser = argparse.ArgumentParser(description="GPT Generals Game Client")
    parser.add_argument("--host", default="localhost", help="Server host address")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--player-name", default="", help="Player name")
    parser.add_argument("--no-lobby", action="store_true", help="Skip lobby and join game directly")

    args = parser.parse_args()

    # Set log level
    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Create and start the client
    client = GameClient(host=args.host, port=args.port)

    # Set a default player name if not provided
    player_name = args.player_name if args.player_name else f"Player_{random.randint(1000, 9999)}"

    # Register callbacks for game state
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

    def on_lobby_state(state):
        rooms = state.get("rooms", [])
        print("\nLobby state updated:")
        print(f"Available rooms: {len(rooms)}")

        for i, room in enumerate(rooms):
            print(f"\nRoom {i + 1}: {room.get('name', 'Unnamed')} (ID: {room.get('id', 'N/A')})")
            print(f"Host: {room.get('hostName', 'Unknown')}")
            print(f"Status: {room.get('status', 'Unknown')}")

            players = room.get("players", [])
            print(f"Players ({len(players)}):")
            for player in players:
                host_tag = " (Host)" if player.get("isHost", False) else ""
                print(f"  - {player.get('name', 'Unknown')}{host_tag}")

    # Register all callbacks
    client.register_state_update_callback(on_state_update)
    client.register_move_result_callback(on_move_result)
    client.register_error_callback(on_error)
    client.register_lobby_state_callback(on_lobby_state)

    # Start the client
    client.start()

    try:
        # Wait for connection
        print("Connecting to server...")
        time.sleep(2)

        # Determine if we should skip the lobby
        if args.no_lobby:
            print("Skipping lobby and joining game directly...")
            get_state_sync(client)
            game_running = True
        else:
            # Enter lobby mode
            print(f"Entering lobby as {player_name}...")
            get_lobby_state_sync(client)

            # Set the player name
            client.player_name = player_name

            # Initial lobby state
            room_id = None
            is_in_room = False
            is_host = False
            game_running = False

            # Show lobby menu
            def show_lobby_menu():
                print("\nLobby Menu:")
                print("1. Refresh lobby")
                print("2. Create new room")
                print("3. Join room")
                print("4. Leave room")
                print("5. Start game (host only)")
                print("6. View your status")
                print("7. Exit")

                if is_in_room and not game_running:
                    # Show additional options for in-room actions
                    if is_host:
                        print("\nYou are the host of the current room.")
                    else:
                        print("\nYou are in a room. Wait for the host to start the game.")

            # Process lobby commands
            while client.running and client.connected and not game_running:
                show_lobby_menu()
                choice = input("\nEnter your choice (1-7): ").strip()

                if choice == "1":
                    print("Refreshing lobby state...")
                    get_lobby_state_sync(client)

                elif choice == "2":
                    if not is_in_room:
                        room_name = input("Enter room name: ").strip() or f"{player_name}'s Room"
                        print(f"Creating room '{room_name}'...")
                        if create_room_sync(client, room_name, player_name):
                            is_in_room = True
                            is_host = True
                            print(f"Room '{room_name}' created.")
                    else:
                        print("You're already in a room. Leave it first to create a new one.")

                elif choice == "3":
                    if not is_in_room:
                        if not client.lobby_state or not client.lobby_state.get("rooms"):
                            print("No rooms available. Try refreshing the lobby.")
                        else:
                            rooms = client.lobby_state.get("rooms", [])
                            print("\nAvailable rooms:")

                            for i, room in enumerate(rooms):
                                if room.get("status") == "waiting":
                                    print(
                                        f"{i + 1}. {room.get('name')} - "
                                        f"Host: {room.get('hostName')}"
                                    )

                            try:
                                room_index = (
                                    int(input("\nEnter room number to join (0 to cancel): ")) - 1
                                )
                                if room_index >= 0 and room_index < len(rooms):
                                    room = rooms[room_index]
                                    if room.get("status") == "waiting":
                                        room_id = room.get("id")
                                        print(f"Joining room '{room.get('name')}'...")
                                        if join_room_sync(client, room_id, player_name):
                                            is_in_room = True
                                            is_host = False
                                            print(f"Joined room '{room.get('name')}'.")
                                    else:
                                        print("Cannot join this room: game already in progress.")
                            except (ValueError, IndexError):
                                print("Invalid selection.")
                    else:
                        print("You're already in a room. Leave it first to join another one.")

                elif choice == "4":
                    if is_in_room:
                        print("Leaving room...")
                        if leave_room_sync(client):
                            is_in_room = False
                            is_host = False
                            print("Left room.")
                    else:
                        print("You're not in a room.")

                elif choice == "5":
                    if is_in_room and is_host:
                        print("Starting game...")
                        if start_game_sync(client):
                            game_running = True
                            print("Game started!")
                    elif is_in_room:
                        print("Only the host can start the game.")
                    else:
                        print("You're not in a room.")

                elif choice == "6":
                    print("\nYour status:")
                    print(f"Name: {player_name}")
                    if is_in_room:
                        print("In room: Yes")
                        print(f"Role: {'Host' if is_host else 'Player'}")

                        # Find the current room in the lobby state
                        if client.lobby_state and client.lobby_state.get("rooms"):
                            current_room = next(
                                (
                                    r
                                    for r in client.lobby_state.get("rooms", [])
                                    if r.get("id") == client.current_room_id
                                ),
                                None,
                            )
                            if current_room:
                                print(f"Room name: {current_room.get('name')}")
                                print(f"Room status: {current_room.get('status')}")

                                players = current_room.get("players", [])
                                print(f"Players in room: {len(players)}")
                                for p in players:
                                    host_tag = " (Host)" if p.get("isHost", False) else ""
                                    print(f"  - {p.get('name')}{host_tag}")
                    else:
                        print("In room: No")

                elif choice == "7":
                    print("Exiting...")
                    break

                else:
                    print("Invalid choice. Please try again.")

                # Short delay to allow for responses from server
                time.sleep(0.5)

        # Game loop - only enter if we're now in a game
        if game_running and client.running and client.connected:
            print("\nEntering game mode...")
            get_state_sync(client)

            # Simple interactive game loop
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
