#!/bin/sh

# make sure we work on the correct folder
#DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
#cd $DIR

# postgres setup
sudo pacman -S postgresql
sudo mkdir -p /var/lib/postgres/data
sudo chown -R postgres:postgres /var/lib/postgres
sudo -iu postgres initdb -D /var/lib/postgres/data
sudo systemctl start postgresql.service

# venv setup
sudo pacman -S gcc
sudo pacman -S python
sudo pacman -S python-virtualenv
virtualenv .venv
source .venv/bin/activate
pip install python-telegram-bot
pip install sqlalchemy
pip install psycopg2
pip install alembic
pip install python-i18n
pip install PyYAML

pip install -e .

# build schema
./bin/reset_db.sh

echo "Setup completed. Remember to stamp the alembic revision table."
