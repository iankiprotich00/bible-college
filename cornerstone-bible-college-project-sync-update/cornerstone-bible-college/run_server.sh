#!/bin/sh
# Starts the portal server so phones on your Wi-Fi can reach it.
cd "$(dirname "$0")"
python3 server.py --host 0.0.0.0
