#!/bin/bash

cd ~/caehlcettel
ACCESS_TOKEN="xxxxxxxxxxxxxxxxxxxxxxxxx" \
API_BASE_URL="http://10.0.0.186:8000" \
poetry run python3 ./caehlcettel.py
