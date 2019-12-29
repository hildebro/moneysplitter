sudo -iu postgres psql -c 'drop database moenysplitter;'
sudo -iu postgres createdb moneysplitter
python init_db.py
