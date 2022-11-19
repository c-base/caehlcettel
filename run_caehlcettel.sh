#!/bin/bash

cd ~/caehlcettel
ACCESS_TOKEN="xxxxxxxxxxxxxxxxxxxxxxxxx" \
API_BASE_URL="https://barpi.cbrp3.c-base.org:8000" \
PRINTER_HOSTNAME="bondruccer.cbrp3.c-base.org" \
COUNT_TYPE="tresencasse"\
poetry run python3 ./caehlcettel.py

echo "Press [ENTER] to close this window."
read
