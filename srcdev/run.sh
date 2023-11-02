#!/usr/bin/with-contenv bashio

export USERNAME=$(bashio::config 'energa_username')
export PASSWORD=$(bashio::config 'energa_password')
export LOGLEVEL=$(bashio::config 'log_level')

bashio::log.info "Uruchamiam API"
python run.py

