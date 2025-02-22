#!/bin/bash

# Add local bin to PATH
export PATH="$HOME/.local/bin:$PATH"

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | CARGO_HOME=~/.local RUSTUP_HOME=~/.local sh
    # Wait a moment for installation to complete
    sleep 2
    # Source the environment file
    . "$HOME/.local/env"
fi

# Create and activate virtual environment
uv venv
. .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Install dev dependencies
uv pip install ruff pyright
