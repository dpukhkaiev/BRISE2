#!/bin/bash

docker-compose down

docker-compose up -d --build

# sshpass -p "root" ssh root@localhost -p 2222 "python3 app.py & python3 main.py"

