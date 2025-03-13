#!/usr/bin/env python3
"""
Main script for playing GPT Generals with client-server architecture.

This script can start the server in the background and run a client,
or it can start either the server or client independently.
"""

import argparse
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_standalone_text_client(host, port):
    """Run a text-based client in standalone mode."""
    import sys

    from game_client import main as run_text_client

    # Update sys.argv to pass the appropriate arguments to the client
    sys.argv = ["game_client.py", "--host", host, "--port", str(port)]

    # Run the text client
    run_text_client()


def run_standalone_tui_client(host, port, manual_mode=False):
    """
    Run a TUI client in standalone mode.

    Args:
        host: Host address of the server
        port: Port number of the server
        manual_mode: Whether to use manual control mode (default False)
    """
    from client_tui import run_client_tui

    # Run the TUI client
    run_client_tui(host=host, port=port, manual_mode=manual_mode)


def run_standalone_server(host, port, width, height, water_probability, num_coins, debug=False):
    """Run a server in standalone mode."""
    import asyncio

    from game_engine import GameEngine
    from game_server import GameServer

    # Set debug logging if requested
    if debug:
        logger.setLevel(logging.DEBUG)

    # Create a game engine first
    game_engine = GameEngine(
        width=width,
        height=height,
        water_probability=water_probability,
        num_coins=num_coins,
    )

    # Create and start the server with the game engine
    server = GameServer(
        game=game_engine,
        host=host,
        port=port,
    )

    # Run the server in the main thread
    logger.info(f"Starting server on {host}:{port}")
    asyncio.run(server.start_server())


def run_integrated_mode(
    host,
    port,
    width,
    height,
    water_probability,
    num_coins,
    client_type="tui",
    manual_mode=False,
    debug=False,
):
    """
    Run the server in the background and a client in the foreground.

    Args:
        host: Host address to bind the server to
        port: Port to bind the server to
        width: Width of the game map
        height: Height of the game map
        water_probability: Probability of water tiles on the map
        num_coins: Number of coins to place on the map
        client_type: Type of client to run ("tui" or "text")
        manual_mode: Whether to use manual control mode (default False)
        debug: Whether to enable debug logging
    """
    from game_engine import GameEngine
    from game_server import GameServer

    # Set debug logging if requested
    if debug:
        logger.setLevel(logging.DEBUG)

    # Create a game engine first
    game_engine = GameEngine(
        width=width,
        height=height,
        water_probability=water_probability,
        num_coins=num_coins,
    )

    # Create the server with the game engine
    server = GameServer(
        game=game_engine,
        host=host,
        port=port,
    )

    # Start the server in a background thread
    server.start()
    logger.info(f"Server started on {host}:{port}")

    # Give the server a moment to initialize
    time.sleep(1)

    try:
        # Start the appropriate client
        if client_type == "tui":
            logger.info("Starting TUI client...")
            from client_tui import run_client_tui

            run_client_tui(host=host, port=port, manual_mode=manual_mode)
        else:
            logger.info("Starting text client...")
            run_standalone_text_client(host, port)

    finally:
        # Make sure to stop the server when the client exits
        logger.info("Stopping server...")
        server.stop()


def main():
    """Parse command-line arguments and run the appropriate mode."""
    parser = argparse.ArgumentParser(description="GPT Generals Game")

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--server", action="store_true", help="Run in server-only mode")
    mode_group.add_argument("--client", action="store_true", help="Run in client-only mode")

    # General options
    parser.add_argument("--host", default="localhost", help="Host address to use")
    parser.add_argument("--port", type=int, default=8765, help="Port to use")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    # Client options
    client_group = parser.add_argument_group("Client options")
    client_group.add_argument(
        "--client-type",
        choices=["text", "tui"],
        default="tui",
        help="Type of client interface (text or tui)",
    )
    client_group.add_argument(
        "--manual", action="store_true", help="Use manual control mode (unit/direction commands)"
    )

    # Server options
    server_group = parser.add_argument_group("Server options")
    server_group.add_argument("--width", type=int, default=10, help="Width of the map")
    server_group.add_argument("--height", type=int, default=10, help="Height of the map")
    server_group.add_argument("--water", type=float, default=0.2, help="Probability of water tiles")
    server_group.add_argument("--coins", type=int, default=5, help="Number of coins on the map")

    args = parser.parse_args()

    # Run in the appropriate mode
    if args.server:
        # Server-only mode
        run_standalone_server(
            host=args.host,
            port=args.port,
            width=args.width,
            height=args.height,
            water_probability=args.water,
            num_coins=args.coins,
            debug=args.debug,
        )
    elif args.client:
        # Client-only mode
        if args.client_type == "tui":
            run_standalone_tui_client(args.host, args.port, args.manual)
        else:
            run_standalone_text_client(args.host, args.port)
    else:
        # Integrated mode (default)
        run_integrated_mode(
            host=args.host,
            port=args.port,
            width=args.width,
            height=args.height,
            water_probability=args.water,
            num_coins=args.coins,
            client_type=args.client_type,
            manual_mode=args.manual,
            debug=args.debug,
        )


if __name__ == "__main__":
    main()
