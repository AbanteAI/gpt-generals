#!/usr/bin/env python3
"""
WebSocket server for GPT Generals game.

This module implements a server that manages the game state and handles
client connections via WebSockets.
"""

from __future__ import annotations

import asyncio
import json
import logging
import signal
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

import websockets

from game_engine import GameEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@dataclass
class GameCommand:
    """Command sent from client to server."""

    command: str
    unit_name: Optional[str] = None
    direction: Optional[str] = None
    player_id: Optional[str] = None


@dataclass
class GameRoom:
    """Represents a game room in the lobby."""

    id: str
    name: str
    host_id: str
    host_name: str
    players: Dict[str, Dict[str, Any]]
    status: str  # 'waiting', 'playing', 'finished'
    created_at: int
    game: Optional[GameEngine] = None


class GameServer:
    """WebSocket server for GPT Generals game."""

    def __init__(
        self,
        game: Optional[GameEngine] = None,
        host: str = "localhost",
        port: int = 8765,
        enable_lobby: bool = True,
    ):
        """
        Initialize the game server.

        Args:
            game: GameEngine instance to use for the game (optional if using lobby)
            host: Host address to bind the server to
            port: Port to bind the server to
            enable_lobby: Whether to enable the lobby functionality
        """
        self.host = host
        self.port = port
        self.enable_lobby = enable_lobby

        # Default game parameters
        self.default_width = 10
        self.default_height = 10
        self.default_water_probability = 0.2
        self.default_num_coins = 5

        # Store the game engine (or create a default one if not provided)
        if game:
            self.game = game
            self.width = game.width
            self.height = game.height
            self.water_probability = 0.2  # Default value
            self.num_coins = len(game.coin_positions)
        else:
            # Create a default game if none provided
            self.game = GameEngine(
                width=self.default_width,
                height=self.default_height,
                water_probability=self.default_water_probability,
                num_coins=self.default_num_coins,
            )
            self.width = self.default_width
            self.height = self.default_height
            self.water_probability = self.default_water_probability
            self.num_coins = self.default_num_coins

        # Keep track of connected clients with their metadata
        self.clients: Dict["websockets.WebSocketServerProtocol", Dict[str, Any]] = {}

        # Server state
        self.server_running = False
        self.server_task: Optional[asyncio.Task] = None
        self.server_thread: Optional[threading.Thread] = None

        # Game rooms for lobby
        self.rooms: Dict[str, GameRoom] = {}

    async def register(self, websocket: "websockets.WebSocketServerProtocol") -> None:
        """Register a new client connection."""
        client_id = str(uuid.uuid4())
        self.clients[websocket] = {
            "id": client_id,
            "name": f"Player_{client_id[:6]}",  # Default name
            "room_id": None,
            "player_id": None,
            "color": None,
        }
        logger.info(f"Client {client_id} connected. Total clients: {len(self.clients)}")

        # If lobby is disabled, assign player to the main game
        if not self.enable_lobby:
            # Assign a player to this client
            player_name = f"Player {len(self.clients)}"
            player_id = self.game.add_player(player_name)

            # Add a unit for the new player
            try:
                unit_name = self.game.add_unit(player_id)
                logger.info(f"Added player {player_name} (ID: {player_id}) with unit {unit_name}")

                # Associate the player ID with this websocket
                self.clients[websocket]["player_id"] = player_id
            except ValueError as e:
                logger.warning(f"Could not add unit for new player: {e}")

            # Send the current game state to the new client
            await self.send_game_state(websocket)
        else:
            # Send the lobby state to the new client
            await self.send_lobby_state(websocket)

    async def unregister(self, websocket: "websockets.WebSocketServerProtocol") -> None:
        """Unregister a client connection."""
        if websocket in self.clients:
            client_info = self.clients[websocket]
            client_id = client_info["id"]
            room_id = client_info.get("room_id")

            # If client was in a room, remove them
            if room_id and room_id in self.rooms:
                room = self.rooms[room_id]
                player_id = client_info.get("player_id")
                if player_id and player_id in room.players:
                    del room.players[player_id]

                    # If the room is now empty, remove it
                    if not room.players:
                        del self.rooms[room_id]
                    # If host left, assign a new host or remove the room
                    elif room.host_id == client_id:
                        if room.players:
                            # Assign first remaining player as host
                            new_host_id = next(iter(room.players.keys()))
                            new_host = room.players[new_host_id]
                            room.host_id = new_host_id
                            room.host_name = new_host["name"]
                            room.players[new_host_id]["is_host"] = True
                        else:
                            # No players left, remove the room
                            del self.rooms[room_id]

                    # Update lobby state for all clients
                    await self.broadcast_lobby_state()

            # Remove the client
            del self.clients[websocket]
            logger.info(f"Client {client_id} disconnected. Remaining clients: {len(self.clients)}")

    def serialize_game_state(self, game: Optional[GameEngine] = None) -> Dict[str, Any]:
        """
        Serialize the current game state to a JSON-compatible dictionary.

        Args:
            game: Optional game engine to serialize. If None, uses the default game.

        Returns:
            Dictionary containing the current game state
        """
        if game is None:
            game = self.game

        # Convert TerrainType enum to string - use enum name instead of value
        # This ensures the frontend gets "WATER" or "LAND" instead of "~" or "."
        map_grid_serialized = [[cell.name for cell in row] for row in game.map_grid]

        # Convert units dictionary to serializable format
        units_serialized = {
            name: {"name": unit.name, "position": unit.position, "player_id": unit.player_id}
            for name, unit in game.units.items()
        }

        # Convert players dictionary to serializable format
        players_serialized = {
            id: {"id": player.id, "name": player.name, "color": player.color}
            for id, player in game.players.items()
        }

        return {
            "type": "game_state",
            "map_grid": map_grid_serialized,
            "units": units_serialized,
            "players": players_serialized,
            "coin_positions": game.coin_positions,
            "current_turn": game.current_turn,
            "width": game.width,
            "height": game.height,
        }

    def serialize_lobby_state(self) -> Dict[str, Any]:
        """
        Serialize the current lobby state to a JSON-compatible dictionary.

        Returns:
            Dictionary containing the current lobby state
        """
        rooms_serialized = []
        for _room_id, room in self.rooms.items():
            rooms_serialized.append(
                {
                    "id": room.id,
                    "name": room.name,
                    "hostId": room.host_id,
                    "hostName": room.host_name,
                    "players": [
                        {
                            "id": player_id,
                            "name": player_info["name"],
                            "color": player_info["color"],
                            "isHost": player_info["is_host"],
                        }
                        for player_id, player_info in room.players.items()
                    ],
                    "status": room.status,
                    "createdAt": room.created_at,
                }
            )

        return {"type": "lobby_state", "rooms": rooms_serialized}

    async def send_game_state(
        self,
        websocket: Optional["websockets.WebSocketServerProtocol"] = None,
        room_id: Optional[str] = None,
    ) -> None:
        """
        Send the current game state to clients.

        Args:
            websocket: Specific client to send state to, or None to broadcast to all
            room_id: Room ID to broadcast to, or None for main game
        """
        # Determine which game to send
        game = self.game
        if room_id and room_id in self.rooms and self.rooms[room_id].game:
            game = self.rooms[room_id].game

        state_data = self.serialize_game_state(game)
        state_json = json.dumps(state_data)

        if websocket:
            # Send to the specific client
            await websocket.send(state_json)
        else:
            # Broadcast to all clients in the room or all clients if no room specified
            websockets_to_remove = set()
            for client, client_info in self.clients.items():
                # Skip clients not in the specified room if a room is specified
                if room_id and client_info.get("room_id") != room_id:
                    continue

                try:
                    await client.send(state_json)
                except websockets.exceptions.ConnectionClosed:
                    # Mark client for removal
                    websockets_to_remove.add(client)

            # Remove any closed connections
            for client in websockets_to_remove:
                await self.unregister(client)

    async def send_lobby_state(
        self, websocket: Optional["websockets.WebSocketServerProtocol"] = None
    ) -> None:
        """
        Send the current lobby state to clients.

        Args:
            websocket: Specific client to send state to, or None to broadcast to all
        """
        state_data = self.serialize_lobby_state()
        state_json = json.dumps(state_data)

        if websocket:
            # Send to the specific client
            await websocket.send(state_json)
        else:
            await self.broadcast_lobby_state()

    async def broadcast_lobby_state(self) -> None:
        """Broadcast the lobby state to all connected clients."""
        state_data = self.serialize_lobby_state()
        state_json = json.dumps(state_data)

        # Broadcast to all clients
        websockets_to_remove = set()
        for client in self.clients:
            try:
                await client.send(state_json)
            except websockets.exceptions.ConnectionClosed:
                # Mark client for removal
                websockets_to_remove.add(client)

        # Remove any closed connections
        for client in websockets_to_remove:
            await self.unregister(client)

    async def process_command(
        self, websocket: "websockets.WebSocketServerProtocol", message_data: Dict[str, Any]
    ) -> None:
        """
        Process a command from a client.

        Args:
            websocket: WebSocket connection from the client
            message_data: Dictionary containing the command
        """
        try:
            command = message_data.get("command")
            if not command:
                await websocket.send(json.dumps({"type": "error", "message": "Missing command"}))
                return

            # Handle lobby commands
            if self.enable_lobby and command.startswith("lobby_"):
                await self.process_lobby_command(websocket, command, message_data)
                return

            # Game commands
            if command == "move":
                # Get client info
                client_info = self.clients.get(websocket, {})
                room_id = client_info.get("room_id")

                # Determine which game to use
                game = self.game
                if room_id and room_id in self.rooms and self.rooms[room_id].game:
                    game = self.rooms[room_id].game

                unit_name = message_data.get("unit_name")
                direction = message_data.get("direction")

                if not unit_name or not direction:
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "error",
                                "message": "Missing unit_name or direction for move command",
                            }
                        )
                    )
                    return

                # Try to move the unit
                # Get the player_id associated with this client
                player_id = client_info.get("player_id")

                # Ensure game is not None
                if game is None:
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "error",
                                "message": "Game not found",
                            }
                        )
                    )
                    return

                success = game.move_unit(unit_name, direction, player_id)

                if success:
                    # If move was successful, advance turn
                    game.next_turn()

                    # Send success message to the client who made the move
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "move_result",
                                "success": True,
                                "unit_name": unit_name,
                                "direction": direction,
                            }
                        )
                    )

                    # Broadcast the updated game state to all clients in the room
                    await self.send_game_state(room_id=room_id)
                else:
                    # Send failure message to the client
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "move_result",
                                "success": False,
                                "unit_name": unit_name,
                                "direction": direction,
                                "message": f"Invalid move: {unit_name} cannot move {direction}",
                            }
                        )
                    )

            elif command == "chat":
                # Get client info
                client_info = self.clients.get(websocket, {})
                room_id = client_info.get("room_id")

                sender = message_data.get("sender")
                content = message_data.get("content")
                sender_type = message_data.get("sender_type", "player")

                if not sender or not content:
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "error",
                                "message": "Missing sender or content for chat command",
                            }
                        )
                    )
                    return

                # Create a chat message to broadcast
                chat_message = {
                    "type": "chat_message",
                    "sender": sender,
                    "content": content,
                    "sender_type": sender_type,
                    "timestamp": str(int(time.time())),
                }

                # Broadcast the chat message to clients in the same room or all if no room
                chat_json = json.dumps(chat_message)
                websockets_to_remove = set()
                for client, client_info in self.clients.items():
                    # Skip clients not in the same room if a room is specified
                    if room_id and client_info.get("room_id") != room_id:
                        continue

                    try:
                        await client.send(chat_json)
                    except websockets.exceptions.ConnectionClosed:
                        # Mark client for removal
                        websockets_to_remove.add(client)

                # Remove any closed connections
                for client in websockets_to_remove:
                    await self.unregister(client)

                # Send acknowledgment to the original sender
                await websocket.send(
                    json.dumps(
                        {"type": "chat_result", "success": True, "message": "Chat message sent"}
                    )
                )

            elif command == "get_state":
                # Get client info
                client_info = self.clients.get(websocket, {})
                room_id = client_info.get("room_id")

                # If in a room, send that game state, otherwise send the main game state
                if room_id and room_id in self.rooms and self.rooms[room_id].game:
                    game = self.rooms[room_id].game
                    state_data = self.serialize_game_state(game)
                    await websocket.send(json.dumps(state_data))
                else:
                    await self.send_game_state(websocket)

            elif command == "get_lobby_state":
                # Send the current lobby state to the client
                await self.send_lobby_state(websocket)

            elif command == "reset":
                # Get client info to check if in a room
                client_info = self.clients.get(websocket, {})
                room_id = client_info.get("room_id")

                # Reset the specified game with the same settings
                if room_id and room_id in self.rooms:
                    room = self.rooms[room_id]
                    # Only the host can reset the game
                    if client_info["id"] == room.host_id:
                        # Create a new game with the same settings
                        room.game = GameEngine(
                            width=self.width,
                            height=self.height,
                            water_probability=self.water_probability,
                            num_coins=self.num_coins,
                        )
                        room.status = "waiting"

                        # Broadcast the new game state to all clients in the room
                        await self.send_game_state(room_id=room_id)
                        await self.broadcast_lobby_state()

                        # Send acknowledgment to the client
                        await websocket.send(json.dumps({"type": "reset_result", "success": True}))
                    else:
                        await websocket.send(
                            json.dumps(
                                {
                                    "type": "error",
                                    "message": "Only the room host can reset the game",
                                }
                            )
                        )
                else:
                    # Reset the main game
                    new_game = GameEngine(
                        width=self.width,
                        height=self.height,
                        water_probability=self.water_probability,
                        num_coins=self.num_coins,
                    )
                    self.game = new_game

                    # Broadcast the new game state to all clients
                    await self.send_game_state()

                    # Send acknowledgment to the client
                    await websocket.send(json.dumps({"type": "reset_result", "success": True}))

            else:
                await websocket.send(
                    json.dumps({"type": "error", "message": f"Unknown command: {command}"})
                )

        except Exception as e:
            logger.error(f"Error processing command: {e}")
            await websocket.send(
                json.dumps({"type": "error", "message": f"Server error: {str(e)}"})
            )

    async def process_lobby_command(
        self,
        websocket: "websockets.WebSocketServerProtocol",
        command: str,
        message_data: Dict[str, Any],
    ) -> None:
        """
        Process a lobby-related command from a client.

        Args:
            websocket: WebSocket connection from the client
            command: Command to process
            message_data: Dictionary containing the command data
        """
        client_info = self.clients.get(websocket, {})
        client_id = client_info["id"]

        if command == "lobby_create_room":
            # Create a new game room
            room_name = message_data.get("room_name", f"Room {len(self.rooms) + 1}")
            player_name = message_data.get(
                "player_name", client_info.get("name", f"Player_{client_id[:6]}")
            )
            player_color = message_data.get("player_color", "#F44336")  # Default red

            # Update client info
            client_info["name"] = player_name
            client_info["color"] = player_color

            # Create a unique room ID
            room_id = str(uuid.uuid4())

            # Create the room
            room = GameRoom(
                id=room_id,
                name=room_name,
                host_id=client_id,
                host_name=player_name,
                players={client_id: {"name": player_name, "color": player_color, "is_host": True}},
                status="waiting",
                created_at=int(time.time()),
                game=None,  # Game will be created when starting
            )

            # Add the room
            self.rooms[room_id] = room

            # Update client's room assignment
            client_info["room_id"] = room_id

            # Send success response
            await websocket.send(
                json.dumps(
                    {
                        "type": "room_created",
                        "success": True,
                        "room_id": room_id,
                        "room_name": room_name,
                    }
                )
            )

            # Broadcast updated lobby state to all clients
            await self.broadcast_lobby_state()

        elif command == "lobby_join_room":
            room_id = message_data.get("room_id")
            player_name = message_data.get(
                "player_name", client_info.get("name", f"Player_{client_id[:6]}")
            )
            player_color = message_data.get("player_color", "#2196F3")  # Default blue

            if not room_id or room_id not in self.rooms:
                await websocket.send(json.dumps({"type": "error", "message": "Invalid room ID"}))
                return

            room = self.rooms[room_id]

            # Check if the room is joinable
            if room.status != "waiting":
                await websocket.send(
                    json.dumps(
                        {"type": "error", "message": "Cannot join room: game already in progress"}
                    )
                )
                return

            # Update client info
            client_info["name"] = player_name
            client_info["color"] = player_color
            client_info["room_id"] = room_id

            # Add player to room
            room.players[client_id] = {"name": player_name, "color": player_color, "is_host": False}

            # Send success response
            await websocket.send(
                json.dumps(
                    {
                        "type": "room_joined",
                        "success": True,
                        "room_id": room_id,
                        "room_name": room.name,
                    }
                )
            )

            # Broadcast updated lobby state to all clients
            await self.broadcast_lobby_state()

        elif command == "lobby_leave_room":
            room_id = client_info.get("room_id")

            if not room_id or room_id not in self.rooms:
                await websocket.send(
                    json.dumps({"type": "error", "message": "Not in a valid room"})
                )
                return

            room = self.rooms[room_id]

            # Remove player from room
            if client_id in room.players:
                del room.players[client_id]

            # Update client info
            client_info["room_id"] = None

            # If room is now empty, remove it
            if not room.players:
                del self.rooms[room_id]
            # If host left, assign a new host
            elif room.host_id == client_id:
                if room.players:
                    # Assign first remaining player as host
                    new_host_id = next(iter(room.players.keys()))
                    new_host = room.players[new_host_id]
                    room.host_id = new_host_id
                    room.host_name = new_host["name"]
                    room.players[new_host_id]["is_host"] = True

            # Send success response
            await websocket.send(json.dumps({"type": "room_left", "success": True}))

            # Broadcast updated lobby state to all clients
            await self.broadcast_lobby_state()

        elif command == "lobby_start_game":
            room_id = client_info.get("room_id")

            if not room_id or room_id not in self.rooms:
                await websocket.send(
                    json.dumps({"type": "error", "message": "Not in a valid room"})
                )
                return

            room = self.rooms[room_id]

            # Check if requester is the host
            if client_id != room.host_id:
                await websocket.send(
                    json.dumps({"type": "error", "message": "Only the host can start the game"})
                )
                return

            # Create a new game for this room
            game = GameEngine(
                width=self.width,
                height=self.height,
                water_probability=self.water_probability,
                num_coins=self.num_coins,
            )

            # Add all players in the room to the game
            player_ids = {}
            for player_id, player_info in room.players.items():
                # Add the player (add_player only takes a name parameter)
                game_player_id = game.add_player(player_info["name"])

                # Manually update the player's color after creation
                if game_player_id in game.players:
                    game.players[game_player_id].color = player_info["color"]

                player_ids[player_id] = game_player_id

                # Add a unit for the player
                try:
                    unit_name = game.add_unit(game_player_id)
                    logger.info(f"Added player {player_info['name']} with unit {unit_name}")

                    # Find the websocket for this player
                    for _ws, info in self.clients.items():
                        if info["id"] == player_id:
                            info["player_id"] = game_player_id
                            break

                except ValueError as e:
                    logger.warning(f"Could not add unit for player: {e}")

            # Set the game and update status
            room.game = game
            room.status = "playing"

            # Send success response
            await websocket.send(
                json.dumps({"type": "game_started", "success": True, "room_id": room_id})
            )

            # Broadcast updated game state to players in the room
            await self.send_game_state(room_id=room_id)

            # Broadcast updated lobby state to all clients
            await self.broadcast_lobby_state()

        elif command == "lobby_set_player_info":
            player_name = message_data.get("player_name")
            player_color = message_data.get("player_color")

            if player_name:
                client_info["name"] = player_name

            if player_color:
                client_info["color"] = player_color

            # If in a room, update the player info in the room
            room_id = client_info.get("room_id")
            if room_id and room_id in self.rooms:
                room = self.rooms[room_id]
                if client_id in room.players:
                    if player_name:
                        room.players[client_id]["name"] = player_name
                        # If this player is host, update host name too
                        if client_id == room.host_id:
                            room.host_name = player_name

                    if player_color:
                        room.players[client_id]["color"] = player_color

                # Broadcast updated lobby state
                await self.broadcast_lobby_state()

            # Send success response
            await websocket.send(json.dumps({"type": "player_info_updated", "success": True}))

        else:
            await websocket.send(
                json.dumps({"type": "error", "message": f"Unknown lobby command: {command}"})
            )

    async def handler(self, websocket: "websockets.WebSocketServerProtocol") -> None:
        """
        Handle a client connection.

        Args:
            websocket: WebSocket connection from the client
        """
        # Register the client
        await self.register(websocket)

        try:
            # Handle messages from the client
            async for message in websocket:
                try:
                    message_data = json.loads(message)
                    await self.process_command(websocket, message_data)
                except json.JSONDecodeError:
                    await websocket.send(
                        json.dumps({"type": "error", "message": "Invalid JSON format"})
                    )
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            # Unregister the client when the connection is closed
            await self.unregister(websocket)

    async def start_server(self) -> None:
        """Start the WebSocket server."""
        self.server_running = True
        logger.info(f"Starting server on {self.host}:{self.port}")

        # Start the server
        async with websockets.serve(self.handler, self.host, self.port):
            # Set up signal handlers for graceful shutdown
            loop = asyncio.get_running_loop()
            loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(self.shutdown()))
            loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(self.shutdown()))

            # Keep the server running
            while self.server_running:
                await asyncio.sleep(1)

    async def shutdown(self) -> None:
        """Shutdown the server gracefully."""
        logger.info("Shutting down server...")
        self.server_running = False

        # Close all client connections
        if self.clients:
            await asyncio.gather(*[client.close() for client in self.clients])
            self.clients.clear()

    def start(self) -> None:
        """Start the server in a separate thread."""
        if self.server_thread is not None and self.server_thread.is_alive():
            logger.warning("Server is already running")
            return

        # Create a new event loop for the thread
        def run_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.server_task = loop.create_task(self.start_server())
            try:
                loop.run_until_complete(self.server_task)
            except asyncio.CancelledError:
                pass
            finally:
                loop.close()

        # Start the server in a new thread
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        logger.info("Server started in background thread")

    def stop(self) -> None:
        """Stop the server."""
        if self.server_thread is None or not self.server_thread.is_alive():
            logger.warning("Server is not running")
            return

        # Set server_running to False
        self.server_running = False

        # Join the thread
        if self.server_thread is not None:
            self.server_thread.join(timeout=5)
            if self.server_thread.is_alive():
                logger.warning("Server thread did not terminate gracefully")
            else:
                logger.info("Server stopped")
            self.server_thread = None


def main():
    """Run the server as a standalone application."""
    import argparse

    parser = argparse.ArgumentParser(description="GPT Generals Game Server")
    parser.add_argument("--host", default="localhost", help="Host address to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind to")
    parser.add_argument("--width", type=int, default=10, help="Width of the game map")
    parser.add_argument("--height", type=int, default=10, help="Height of the game map")
    parser.add_argument("--water", type=float, default=0.2, help="Probability of water tiles")
    parser.add_argument("--coins", type=int, default=5, help="Number of coins on the map")
    parser.add_argument("--no-lobby", action="store_true", help="Disable lobby feature")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Set log level
    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Create game engine if lobby is disabled
    game_engine = None
    if args.no_lobby:
        game_engine = GameEngine(
            width=args.width,
            height=args.height,
            water_probability=args.water,
            num_coins=args.coins,
        )

    # Create and start the server
    server = GameServer(
        game=game_engine,
        host=args.host,
        port=args.port,
        enable_lobby=not args.no_lobby,
    )

    # Run the server in the main thread
    asyncio.run(server.start_server())


if __name__ == "__main__":
    main()
