#!/bin/bash
# source this
if [ -z "$1" ]
  then
    j_host=172.19.0.2
  else
    j_host=$1
fi

export TEMPO_HOST=${j_host}
echo "TEMPO_HOST:" ${TEMPO_HOST}
export CELERY_RUN=Y
celery -A tasks worker --loglevel=info