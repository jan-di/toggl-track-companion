#!/bin/bash

component=$1

source /venv/bin/activate

start_web () {
  echo "Start Web"

  gunicorn 'web_prod:start()'
}

start_updater () {
  echo "Start Updater"

  python3 updater.py
}

unknown () {
  echo "Invalid Component"
}

case "$component" in
    web)
        start_web
        ;;
    updater)
        start_updater
        ;;
    *)
        unknown
        ;;
esac
