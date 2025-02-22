#!/bin/bash

# Activate virtual environment
. .venv/bin/activate

# Run formatters and linters with fix flags
ruff format .
ruff check --fix .

# Run type checker
pyright
