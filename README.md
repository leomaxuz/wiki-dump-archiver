# wiki-dump-archiver

Simple Python tool to:
- Download Wikimedia dump
- Extract URLs from `.gz` file
- Fetch and save page content to a SQLite database

## How to use
```bash
pip install -r requirements.txt

## Config. get.py
```bash
DB_PATH = 'data/wiki_pages.db'
DUMP_URL = 'https://dumps.wikimedia.org/other/shorturls/shorturls-20250728.gz'
GZ_FILE = 'data/dumps/shorturls-20250728.gz'

## Run
python get.py
