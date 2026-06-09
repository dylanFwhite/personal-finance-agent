#!/bin/bash

# TODO: Include runtime env setup (uv + python etc.)

# Define the desired path structure (using HOME for standard Linux/Mac location)
DATA_DIR="$HOME/.finance-agent/"

# 1. Ensure the directory exists
mkdir -p "$DATA_DIR"

echo "Ensuring data directory exists at: $DATA_DIR"

# 2. Pass the absolute path as an argument to the Python script
PYTHON_ARGS="--data-dir \"$DATA_DIR\""

# 3. Execute the Python script
python3 main.py ${PYTHON_ARGS}
