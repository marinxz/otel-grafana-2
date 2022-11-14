#!/bin/bash
# use this to run containers locally
container=$1
case $container in
  'grafana')
    docker-compose -f docker-compose-grafana.yml up grafana loki tempo
    ;;
  'redis')
    docker-compose -f docker-compose-redis.yml up
    ;;
  'redis-only')
    docker-compose -f docker-compose-redis.yml up redis 
    ;;
  'ips')
    echo "loki"
    docker ps -qf "name=loki" | xargs -n 1 docker inspect | grep IPAddress
    echo "tempo"
    docker ps -qf "name=tempo" | xargs -n 1 docker inspect | grep IPAddress
    echo "redis"
    docker ps -qf "name=redis" | xargs -n 1 docker inspect | grep IPAddress

    ;;
  'down-redis')
    docker-compose -f docker-compose-redis.yml down
    ;;
  'down-grafana')
    docker-compose -f docker-compose-grafana.yml down
    ;;
  *)
    echo -n "unknown parameter:  "
    echo "down-api down-p build vault api worker peripheral"
    ;;
esac
