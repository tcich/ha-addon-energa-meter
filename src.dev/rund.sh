#!/bin/bash

USERNAME="$ENERGA_USERNAME"
PASSWORD="$ENERGA_PASSWORD"

if [ -z "$USERNAME" ]; then
    echo "Błąd: Zmienna ENERGA_USERNAME jest pusta. Proszę podać wartość."
    exit 1
fi

if [ -z "$PASSWORD" ]; then
    echo "Błąd: Zmienna ENERGA_PASSWORD jest pusta. Proszę podać wartość."
    exit 1
fi

echo "Uruchamiam API"
python api.py &
echo "Uruchamiam MAIN"
python main.py
echo "Uruchamiam CRON"

while true; do
    python cron.py
    echo "Czekam..."
    sleep 1800
done
