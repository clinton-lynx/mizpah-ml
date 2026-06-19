#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
# DeepFace might install opencv-python, which lacks system dependencies on standard Render environments.
# We replace it with opencv-python-headless.
pip uninstall -y opencv-python
pip install opencv-python-headless
