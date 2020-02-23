#!/usr/bin/env bash

# kill any existing instances of the server
pkill -f "python3 manage.py"

# run new server
python3 manage.py runsslserver 0.0.0.0:1337 --certificate localhost.pem --key localhost-key.pem
# python3 manage.py runsslserver 0.0.0.0:1337
