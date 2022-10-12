# run servers 
docker-compose -f docker-compose-grafana.yml up loki grafana tempo


# find IP addreess for the service 

docker ps -qf "name=loki" | xargs -n 1 docker inspect | grep IPAddress
docker ps -qf "name=tempo" | xargs -n 1 docker inspect | grep IPAddress