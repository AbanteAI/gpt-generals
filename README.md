# GPT Generals

A game project that leverages Large Language Models (LLMs), developed by Mentat.

## About

GPT Generals is an innovative gaming project that integrates artificial intelligence through the use of Large Language Models. The project is being developed by Mentat to explore new possibilities in AI-driven gaming experiences.

## Features

- Grid-based map generation with land and water tiles
- Units that can move in four directions (up, down, left, right)
- Coin collection mechanics
- LLM-powered unit movement for strategic gameplay
- Client-server architecture supporting multiple clients
- TUI (Terminal User Interface) and text-based clients

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate the environment: `.venv/bin/activate` (or `.venv\Scripts\activate` on Windows)
4. Install requirements: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and add your OpenRouter API key

## Running the Game

### Default Mode (Integrated Server and Client)

The easiest way to play is to run the main script, which starts a server in the background and launches a client in the foreground:

```bash
python play_game.py
```

This will start a TUI client by default. To use the text-based client instead:

```bash
python play_game.py --client-type text
```

### Server-Only Mode

To run just the server:

```bash
python play_game.py --server
```

Optional server configuration:
```bash
python play_game.py --server --host 0.0.0.0 --port 8765 --width 15 --height 10 --water 0.15 --coins 8
```

### Client-Only Mode

To run just a client connecting to an existing server:

```bash
python play_game.py --client
```

For the text-based client:
```bash
python play_game.py --client --client-type text
```

To connect to a server on a different host or port:
```bash
python play_game.py --client --host example.com --port 8765
```

## Client Controls

### TUI Client

- Select a unit by pressing its letter (A, B, etc.)
- Move selected unit with arrow keys or WASD
- Press space to pause/resume
- Press h for help
- Press r to reset the game
- Press q to quit

### Text Client

- Enter commands in the format: `move <unit> <direction>`
- Example: `move A up` moves unit A up
- Type `state` to refresh the game state
- Type `reset` to reset the game
- Type `quit` to exit

## Running Simulations

You can run simulations in two modes:

### Random Movement Mode

Units move randomly on the map:

```bash
python simulation.py
```

### LLM-Powered Movement Mode

Units use LLM reasoning to decide their moves:

```bash
python simulation.py --llm
```

### Advanced Usage

```bash
# Run a simulation with LLM movement
python test_scripts/llm_simulation.py

# Run a custom map, 10 turns, with LLM movement
python simulation.py --custom-map --turns 10 --llm
```

## Status

This project is currently under development.
