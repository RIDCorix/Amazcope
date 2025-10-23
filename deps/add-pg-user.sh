docker exec -it postgresql psql -U postgres -c "CREATE USER amazope WITH PASSWORD 'amazope';"
docker exec -it postgresql psql -U postgres -c "CREATE DATABASE amazope OWNER amazope;"
docker exec -it postgresql psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE amazope TO amazope;"
