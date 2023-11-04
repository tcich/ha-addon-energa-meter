#!/bin/bash

USERNAME="$ENERGA_USERNAME"
PASSWORD="$ENERGA_PASSWORD"
LOG_LEVEL="$LOG_LEVEL"

if [ -z "$USERNAME" ]; then
    echo "Błąd: Zmienna ENERGA_USERNAME jest pusta. Proszę podać wartość."
    exit 1
fi

if [ -z "$PASSWORD" ]; then
    echo "Błąd: Zmienna ENERGA_PASSWORD jest pusta. Proszę podać wartość."
    exit 1
fi

if [ -z "$LOG_LEVEL" ]; then
    echo "Błąd: Zmienna LOG_LEVEL jest pusta. Przypisuję wartość domyślną INFO."
    LOG_LEVEL="INFO"
fi

echo "Uruchamiam aplikację"
python run.py
echo "..."
