#!/bin/bash

component=$1

start_web () {
  echo "Start Web"

  python3 web.py
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
