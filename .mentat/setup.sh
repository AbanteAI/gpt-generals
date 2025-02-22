#!/bin/bash

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create and activate virtual environment
uv venv
. .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Install dev dependencies
uv pip install ruff pyright
