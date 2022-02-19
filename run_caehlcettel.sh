#!/bin/bash

cd ~/caehlcettel
ACCESS_TOKEN="xxxxxxxxxxxxxxxxxxxxxxxxx" \
API_BASE_URL="https://barpi.cbrp3.c-base.org:8000" \
poetry run python3 ./caehlcettel.py

echo "Press [ENTER] to close this window."
read
