#!/bin/bash
# Script de inicio optimizado para Fronda Brick en WSL 2
export OLLAMA_HOST=0.0.0.0:11434
export OLLAMA_KEEP_ALIVE=15m
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_MODELS=/home/frondabrick/.ollama/models

# Si ya está corriendo, no duplicar
if pgrep -f "/usr/local/bin/ollama serve" > /dev/null; then
    echo "Ollama ya está corriendo en WSL."
else
    echo "Iniciando daemon de Ollama en WSL..."
    nohup /usr/local/bin/ollama serve > ~/.ollama/ollama.log 2>&1 &
    sleep 2
fi

# Mantener anclada la instancia de WSL en background
nohup sleep 86400 >/dev/null 2>&1 &
echo "WSL listo y optimizado."
