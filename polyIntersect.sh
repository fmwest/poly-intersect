#!/bin/bash

case "$1" in
    develop)
        type docker-compose >/dev/null 2>&1 || { echo >&2 "docker-compose is required but it's not installed.  Aborting."; exit 1; }
        docker-compose -f docker-compose-develop.yml build && docker-compose --verbose -f docker-compose-develop.yml up
        ;;
    test)
        type docker-compose >/dev/null 2>&1 || { echo >&2 "docker-compose is required but it's not installed.  Aborting."; exit 1; }
        docker-compose -f docker-compose-test.yml run test
        ;;
    *)
        echo "Usage: polyIntersect.sh {develop|test}" >&2
        exit 1
        ;;
esac

exit 0
