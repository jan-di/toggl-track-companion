#!/bin/bash

component=$1

start_bot () {
  echo "Start Bot"

  python3 bot.py
}

start_web () {
  echo "Start Web"

  python3 web.py
}

unknown () {
  echo "Invalid Component"
}

case "$component" in
    bot)
        start_bot
        ;;
    web)
        start_web
        ;;
    *)
        unknown
        ;;
esac
