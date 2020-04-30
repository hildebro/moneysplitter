#!/bin/sh

# make sure we work on the correct folder
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd $DIR

# postgres setup
sudo pacman -S postgresql --noconfirm
sudo -iu postgres initdb -D /var/lib/postgres/data
sudo systemctl start postgresql.service

# venv setup
virtualenv .venv
source .venv/bin/activate
pip install python-telegram-bot
pip install sqlalchemy
pip install psycopg2
pip install alembic
pip install i18n
pip install PyYAML

# build schema
./reset_db.sh

echo "Setup completed."
