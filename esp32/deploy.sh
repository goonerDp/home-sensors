#!/bin/bash

# Fail fast: exit on any error, on undefined variables, and on a failure
# anywhere in a pipeline rather than only at its last command.
set -euo pipefail

# Work from the directory this script lives in, no matter where it was called
# from. BASH_SOURCE[0] is the path to this file; cd into its parent.
cd "$(dirname "${BASH_SOURCE[0]}")"

# This script sends all project files to the ESP32 board.
PORTS=(/dev/cu.usbserial-*)

# Check that exactly one matching port exists.
if [ ! -e "${PORTS[0]}" ]; then
    echo "Error: no board found. Check the USB cable."
    exit 1
fi

if [ ${#PORTS[@]} -gt 1 ]; then
    echo "Error: found more than one matching port:"
    printf '%s\n' "${PORTS[@]}"
    echo "Unplug the extra device, or edit this script to pick one."
    exit 1
fi

PORT="${PORTS[0]}"
echo "Found board at $PORT"

FILES=("main.py" "config.py" "bme280_float.py" "ble_sensor.py")

# Check everything is present before touching the board, so a missing file
# cannot leave it with a half-updated set of modules.
for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "Error: $file not found."
        exit 1
    fi
done

for file in "${FILES[@]}"; do
    echo "Copying $file..."
    mpremote connect "$PORT" fs cp "$file" ":$file"
done

echo "Resetting board..."
mpremote connect "$PORT" reset

echo "Done."