#!/bin/bash

[ -r /opt/etc/default/openvpn-manager ] && . /opt/etc/default/openvpn-manager

PYTHON_HOME=${PYTHON_HOME:-"/usr"}
APP_HOME=${APP_HOME:-"/opt/openvpn-manager"}
APP_WORK=${APP_WORK:-"$APP_HOME"}

PID_FILE=${PID_FILE:-"${APP_WORK}/api.pid"}
LOG_FILE=${LOG_FILE:-"/opt/var/log/openvpn-manager-api.log"}
LOCK_FILE=${LOCK_FILE:-"/opt/var/lock/subsys/openvpn-manager-api.lock"}
DB_FILE=${DB_FILE:-"${APP_WORK}/data.db"}

function init() {
  echo -n "Initializing OpenVPN Manager API: "

  cd $APP_HOME
  cat <<EOF | ${PYTHON_HOME}/bin/python -
from api.app import db
db.create_all()
EOF

  [ "$?" -eq "0" ] && echo "[  OK  ]" || ( echo "[FAILED]" && exit 1; )
}

function start() {

  if [ ! -e $DB_FILE ]; then
    init
  fi

  echo -n "Starting OpenVPN Manager API: "

  if [ -e $LOCK_FILE ]; then
    echo "[PASSED]"
  else
    cd $APP_HOME
    ${PYTHON_HOME}/bin/python ${APP_HOME}/api/wsgi.py 2>&1 > $LOG_FILE & echo $! > $PID_FILE
    [ "$?" -eq "0" ] && echo "[  OK  ]" && touch $LOCK_FILE || echo "[FAILED]"
  fi
}

function stop() {
  echo -n "Stopping OpenVPN Manager API: "

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
