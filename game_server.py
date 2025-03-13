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
from dataclasses import dataclass
from typing import Any, Dict, Optional, Set

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


class GameServer:
    """WebSocket server for GPT Generals game."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
        width: int = 10,
        height: int = 10,
        water_probability: float = 0.2,
        num_coins: int = 5,
    ):
        """
        Initialize the game server.

        Args:
            host: Host address to bind the server to
            port: Port to bind the server to
            width: Width of the game map
            height: Height of the game map
            water_probability: Probability of water tiles on the map
            num_coins: Number of coins to place on the map
        """
        self.host = host
        self.port = port
        self.width = width
        self.height = height
        self.water_probability = water_probability
        self.num_coins = num_coins

        # Initialize game
        self.game = GameEngine(
            width=width,
            height=height,
            water_probability=water_probability,
            num_coins=num_coins,
        )

        # Keep track of connected clients
        self.clients: Set["websockets.WebSocketServerProtocol"] = set()

        # Server state
        self.server_running = False
        self.server_task: Optional[asyncio.Task] = None
        self.server_thread: Optional[threading.Thread] = None

    async def register(self, websocket: "websockets.WebSocketServerProtocol") -> None:
        """Register a new client connection."""
        self.clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"Client {client_id} connected. Total clients: {len(self.clients)}")

        # Assign a player to this client if we have more than 2 players (the default)
        if len(self.game.players) <= len(self.clients):
            player_name = f"Player {len(self.clients)}"
            player_id = self.game.add_player(player_name)

            # Add a unit for the new player
            try:
                unit_name = self.game.add_unit(player_id)
                logger.info(f"Added player {player_name} (ID: {player_id}) with unit {unit_name}")

                # Associate the player ID with this websocket
                websocket.player_id = player_id
            except ValueError as e:
                logger.warning(f"Could not add unit for new player: {e}")

        # Send the current game state to the new client
        await self.send_game_state(websocket)

    async def unregister(self, websocket: "websockets.WebSocketServerProtocol") -> None:
        """Unregister a client connection."""
        self.clients.remove(websocket)
        client_id = id(websocket)
        logger.info(f"Client {client_id} disconnected. Remaining clients: {len(self.clients)}")

    def serialize_game_state(self) -> Dict[str, Any]:
        """
        Serialize the current game state to a JSON-compatible dictionary.

        Returns:
            Dictionary containing the current game state
        """
        # Convert TerrainType enum to string
        map_grid_serialized = [[cell.value for cell in row] for row in self.game.map_grid]

        # Convert units dictionary to serializable format
        units_serialized = {
            name: {"name": unit.name, "position": unit.position, "player_id": unit.player_id}
            for name, unit in self.game.units.items()
        }

        # Convert players dictionary to serializable format
        players_serialized = {
            id: {"id": player.id, "name": player.name, "color": player.color}
            for id, player in self.game.players.items()
        }

        return {
            "type": "game_state",
            "map_grid": map_grid_serialized,
            "units": units_serialized,
            "players": players_serialized,
            "coin_positions": self.game.coin_positions,
            "current_turn": self.game.current_turn,
            "width": self.game.width,
            "height": self.game.height,
        }

    async def send_game_state(
        self, websocket: Optional["websockets.WebSocketServerProtocol"] = None
    ) -> None:
        """
        Send the current game state to clients.

        Args:
            websocket: Specific client to send state to, or None to broadcast to all
        """
        state_data = self.serialize_game_state()
        state_json = json.dumps(state_data)

        if websocket:
            # Send to the specific client
            await websocket.send(state_json)
        else:
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

            if command == "move":
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
                # Get the player_id associated with this websocket if it exists
                player_id = getattr(websocket, "player_id", None)
                success = self.game.move_unit(unit_name, direction, player_id)

                if success:
                    # If move was successful, advance turn
                    self.game.next_turn()

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

                    # Broadcast the updated game state to all clients
                    await self.send_game_state()
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

                # Broadcast the chat message to all clients
                chat_json = json.dumps(chat_message)
                websockets_to_remove = set()
                for client in self.clients:
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
                # Send the current game state to the client
                await self.send_game_state(websocket)

            elif command == "reset":
                # Reset the game with the same settings
                self.game = GameEngine(
                    width=self.width,
                    height=self.height,
                    water_probability=self.water_probability,
                    num_coins=self.num_coins,
                )

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
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Set log level
    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Create and start the server
    server = GameServer(
        host=args.host,
        port=args.port,
        width=args.width,
        height=args.height,
        water_probability=args.water,
        num_coins=args.coins,
    )

    # Run the server in the main thread
    asyncio.run(server.start_server())


if __name__ == "__main__":
    main()
