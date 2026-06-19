#!/usr/bin/env bash
# exit on error
set -o errexit

# Ensure cmake is available for dlib compilation
pip install cmake

pip install -r requirements.txt
