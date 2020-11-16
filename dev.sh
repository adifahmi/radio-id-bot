#!/usr/bin/env bash

python main.py && watchmedo shell-command --patterns="*.py;" --recursive --command='python main.py' .
