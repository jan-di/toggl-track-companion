#!/bin/bash

component=$1

start_web () {
  echo "Start Web"

  python3 web.py
}

unknown () {
  echo "Invalid Component"
}

case "$component" in
    web)
        start_web
        ;;
    *)
        unknown
        ;;
esac
