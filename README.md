# GPT Generals

A game project that leverages Large Language Models (LLMs), developed by Mentat.

## About

GPT Generals is an innovative gaming project that integrates artificial intelligence through the use of Large Language Models. The project is being developed by Mentat to explore new possibilities in AI-driven gaming experiences.

## Features

- Grid-based map generation with land and water tiles
- Units that can move in four directions (up, down, left, right)
- Coin collection mechanics
- LLM-powered unit movement for strategic gameplay
- Battle between LLM-controlled and random movement units

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

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate the environment: `.venv/bin/activate` (or `.venv\Scripts\activate` on Windows)
4. Install requirements: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and add your OpenRouter API key

## Status

This project is currently under development.
