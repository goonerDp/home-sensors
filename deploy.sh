#!/bin/bash

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

FILES=("main.py" "config.py" "bme280_float.py")

for file in "${FILES[@]}"; do
    echo "Copying $file..."
    mpremote connect "$PORT" fs cp "$file" ":$file"
done

echo "Done."
