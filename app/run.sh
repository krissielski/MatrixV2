#!/bin/bash

nohup python3 main.py > /dev/null 2>&1 &
echo "Application started in background (PID: $!)"
