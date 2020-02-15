#!/bin/bash

if [ -x "$(command -v python3)" ]; then
  python3 -m unittest discover -s tests
else
  python -m unittest discover -s tests
fi
