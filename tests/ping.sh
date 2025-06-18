#!/bin/bash

curl http://192.168.3.50:11434/api/generate \
  -d '{
    "model": "llama3:8b",
    "prompt": "Repeat: ping",
    "stream": false,
    "options": {
      "temperature": 0,
      "top_p": 1,
      "top_k": 0
    }
  }'
