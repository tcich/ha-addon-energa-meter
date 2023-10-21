#!/usr/bin/with-contenv bashio

export USERNAME=$(bashio::config 'energa_username')
export PASSWORD=$(bashio::config 'energa_password')

bashio::log.info "Uruchamiam API"
python api.py &
bashio::log.info "Uruchamiam MAIN"
python main.py
bashio::log.info "Uruchamiam CRON"

while true; do
    python cron.py
    bashio::log.info "Czekam..."
    sleep 1800
done

