#!/bin/bash
set -euo pipefail

if [[ ! -f /config/config_webrx.py ]] ; then
  cp config_webrx.py /config
fi

rm config_webrx.py
ln -s /config/config_webrx.py .


_term() {
  echo "Caught signal!" 
  kill -TERM "$child" 2>/dev/null
}
    
trap _term SIGTERM SIGINT

python3 openwebrx.py $@ &

child=$! 
wait "$child"
    
