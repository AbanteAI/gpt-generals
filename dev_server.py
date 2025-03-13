#!/usr/bin/env python3
"""
Development server with auto-restart for GPT Generals.

This script monitors the codebase for changes and automatically
restarts the server when files are modified.
"""

import logging
import os
import subprocess
import sys
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class ServerRestartHandler(FileSystemEventHandler):
    """Handler for restarting the server when files change."""

    def __init__(self, server_process, restart_callback):
        """Initialize the handler with the server process and restart callback."""
        self.server_process = server_process
        self.restart_callback = restart_callback
        self.last_event_time = time.time()
        self.debounce_seconds = 1.0  # Debounce events by this many seconds

    def on_any_event(self, event):
        """Handle any file system event."""
        # Skip directory events and hidden files
        if event.is_directory or str(os.path.basename(event.src_path)).startswith("."):
            return

        # Skip if not a Python file
        if not str(event.src_path).endswith(".py"):
            return

        # Debounce multiple events
        current_time = time.time()
        if current_time - self.last_event_time < self.debounce_seconds:
            return
        self.last_event_time = current_time

        logger.info(f"Detected change in {event.src_path}")
        self.restart_callback()


def run_dev_server(args):
    """
    Run the development server with auto-restart.

    Args:
        args: Command-line arguments to pass to the server
    """
    server_process = None
    observer = None

    def start_server():
        """Start the server process."""
        nonlocal server_process
        cmd = [sys.executable, "play_game.py", "--server"] + args
        logger.info(f"Starting server: {' '.join(cmd)}")
        server_process = subprocess.Popen(cmd)
        return server_process

    def restart_server():
        """Restart the server process."""
        nonlocal server_process
        if server_process:
            logger.info("Stopping server...")
            server_process.terminate()
            server_process.wait(timeout=5)
            logger.info("Server stopped")
        start_server()

    try:
        # Start the server initially
        start_server()

        # Set up file watcher
        event_handler = ServerRestartHandler(server_process, restart_server)
        observer = Observer()

        # Watch the current directory for changes
        project_root = Path(__file__).parent
        observer.schedule(event_handler, str(project_root), recursive=True)
        observer.start()

        logger.info("Watching for file changes (press Ctrl+C to quit)...")

        # Keep the script running
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Development server interrupted")

    finally:
        # Clean up
        if observer:
            observer.stop()
            observer.join()

        if server_process:
            logger.info("Stopping server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
            logger.info("Server stopped")


def main():
    """Parse command-line arguments and run the development server."""
    import argparse

    parser = argparse.ArgumentParser(description="GPT Generals Development Server")
    parser.add_argument("--host", default="localhost", help="Host address to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind to")
    parser.add_argument("--width", type=int, default=10, help="Width of the game map")
    parser.add_argument("--height", type=int, default=10, help="Height of the game map")
    parser.add_argument("--water", type=float, default=0.2, help="Probability of water tiles")
    parser.add_argument("--coins", type=int, default=5, help="Number of coins on the map")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Convert args to list of strings for subprocess
    arg_list = []
    if args.host != "localhost":
        arg_list.extend(["--host", args.host])
    if args.port != 8765:
        arg_list.extend(["--port", str(args.port)])
    if args.width != 10:
        arg_list.extend(["--width", str(args.width)])
    if args.height != 10:
        arg_list.extend(["--height", str(args.height)])
    if args.water != 0.2:
        arg_list.extend(["--water", str(args.water)])
    if args.coins != 5:
        arg_list.extend(["--coins", str(args.coins)])
    if args.debug:
        arg_list.append("--debug")

    run_dev_server(arg_list)


if __name__ == "__main__":
    main()
