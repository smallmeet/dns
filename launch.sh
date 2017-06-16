#!/bin/sh

PYTHON=`which python`
CWD=`pwd`
WORKER_NUM=2

start() {
  supervisord -c supervisor.conf
}

stop() {
  supervisorctl -c supervisor.conf shutdown
}

restart() {
  stop
  sleep 1
  start
}

case $1 in
  '' | start)
    start
    ;;
  stop)
    stop
    ;;
  restart)
    restart
    ;;
esac
exit 0
}
