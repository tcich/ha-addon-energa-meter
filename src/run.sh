#!/usr/bin/with-contenv bashio

export USERNAME=$(bashio::config 'energa_username')
export PASSWORD=$(bashio::config 'energa_password')
export LOG_LEVEL=$(bashio::config 'log_level')

bashio::log.info "Uruchamiam API"
source /app/venv/bin/activate
python run.py

