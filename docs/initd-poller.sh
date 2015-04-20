#!/bin/bash

PYTHON_HOME="/volume1/homes/ishtanzar/.python/openvpn-manager"
APP_HOME="/volume1/homes/ishtanzar/web/openvpn-manager"
PID_FILE="${APP_HOME}/poller.pid"
LOG_FILE="/opt/var/log/openvpn-manager-poller.log"
LOCK_FILE="/opt/var/lock/subsys/openvpn-manager-poller.lock"

function start() {
  echo -n "Starting OpenVPN Manager Poller: "

  if [ -e $LOCK_FILE ]; then
    echo "[PASSED]"
  else
    cd $APP_HOME
    ${PYTHON_HOME}/bin/python ${APP_HOME}/poller.py 2>&1 > $LOG_FILE & echo $! > $PID_FILE
    [ "$?" -eq "0" ] && echo "[  OK  ]" && touch $LOCK_FILE || echo "[FAILED]"
  fi
}

function stop() {
  echo -n "Stopping OpenVPN Manager Poller: "

  if [ -r $PID_FILE ]; then
    kill $(cat $PID_FILE) 2>&1 > /dev/null
    rm -f $PID_FILE
    echo "[  OK  ]"
  else
    echo "[PASSED]"
  fi

  [ -e $LOCK_FILE ] && rm -rf $LOCK_FILE
}

case $1 in
  start)
    $1
    ;;
  stop)
    $1
    ;;
  restart)
    stop
    start
    ;;
esac