#!/bin/bash
#cd ~/mydroponic
git pull origin main
docker compose up --build -d
