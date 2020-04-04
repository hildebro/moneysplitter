#!/bin/sh

read -p "DANGER: Do you really want to reset your database? " -n 1 -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  exit 1
fi
echo

sudo -iu postgres psql -c 'drop database moneysplitter;'
sudo -iu postgres createdb moneysplitter
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
python $DIR/init_db.py
