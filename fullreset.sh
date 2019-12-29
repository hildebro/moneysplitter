sudo -iu postgres psql -c 'drop database moneysplitter;'
sudo -iu postgres createdb moneysplitter
python init_db.py
