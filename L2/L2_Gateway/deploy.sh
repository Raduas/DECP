#!/usr/bin/env bash
set -euo pipefail                  # při jakékoli chybě skonči, nepokračuj naslepo

cd /home/admin/project/DECP
git pull --ff-only                 # nový compose a skript; když se historie rozešla, raději selže

cd L2/L2_Gateway
docker compose pull api            # stáhne jen NÁŠ image, ne node-red:latest apod.
docker compose up -d               # restartuje jen kontejnery, kterým se změnil image
docker image prune -f              # smaže staré nepoužívané image, na Pi je málo místa