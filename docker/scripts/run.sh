#!/bin/bash
set -euo pipefail

if [[ ! -f /etc/openwebrx/config_webrx.py ]] ; then
  mkdir -p /etc/openwebrx/
  cp config_webrx.py /etc/openwebrx/
fi
_term() {
  echo "Caught signal!" 
  kill -TERM "$child" 2>/dev/null
}
    
trap _term SIGTERM SIGINT

python3 openwebrx.py $@ &

child=$! 
wait "$child"
    
