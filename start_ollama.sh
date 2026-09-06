#!/bin/bash
export OLLAMA_KEEP_ALIVE=-1
export OLLAMA_LOAD_TIMEOUT=15m
export OLLAMA_HOST=0.0.0.0:11434
export OLLAMA_MODELS=/home/frondabrick/.ollama/models

mkdir -p /home/frondabrick/.ollama/logs
exec /usr/local/bin/ollama serve >> /home/frondabrick/.ollama/logs/ollama.log 2>&1
