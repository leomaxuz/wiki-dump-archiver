import gzip
import json
import requests
import sqlite3
from datetime import datetime
from pathlib import Path
import hashlib

# === CONFIGURATION ===
# Set dump URL and local file path here
DB_PATH = 'data/wiki_pages.db'
DUMP_URL = 'https://dumps.wikimedia.org/other/shorturls/shorturls-20250728.gz'
GZ_FILE = 'data/dumps/shorturls-20250728.gz'
# =====================

def init_db(db_path):
    """
    Initialize SQLite database and create the 'pages' table if it doesn't exist.
    """
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS pages (
            url TEXT PRIMARY KEY,
            content TEXT,
            hash TEXT,
            updated_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def download_dump(url, save_path):
    """
    Download the dump file from the given URL if it doesn't already exist locally.
    """
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    if save_path.exists():
        print(f"✅ Already exists: {save_path}")
        return
    print(f"⬇️ Downloading: {url}")
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(save_path, 'wb') as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    print(f"✅ Downloaded: {save_path}")

def extract_urls_from_gz(gz_file):
    """
    Read the .gz file and extract URLs line by line.
    """
    urls = []
    with gzip.open(gz_file, 'rt', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parts = line.strip().split('|', 1)
            if len(parts) == 2:
                urls.append(parts[1])
    print(f"🔍 Found: {len(urls)} URLs")
    return urls

def compute_hash(text):
    """
    Compute SHA-256 hash of the given text.
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def fetch_and_save_to_db(db_path, url):
    """
    Fetch page content by URL and save to DB if new or updated.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        content = r.text
        page_hash = compute_hash(content)
        now = datetime.utcnow().isoformat()

        # Check if page already exists in DB
        c.execute('SELECT hash FROM pages WHERE url=?', (url,))
        row = c.fetchone()

        if row is None:
            # New page
            c.execute('INSERT INTO pages (url, content, hash, updated_at) VALUES (?, ?, ?, ?)',
                      (url, content, page_hash, now))
            print(f"🆕 Added: {url}")
        elif row[0] != page_hash:
            # Updated page
            c.execute('UPDATE pages SET content=?, hash=?, updated_at=? WHERE url=?',
                      (content, page_hash, now, url))
            print(f"🔄 Updated: {url}")
        else:
            print(f"✅ Unchanged: {url}")

        conn.commit()
    except Exception as e:
        print(f"⚠️ Error: {url} -> {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db(DB_PATH)
    download_dump(DUMP_URL, GZ_FILE)

    urls = extract_urls_from_gz(GZ_FILE)
    total = len(urls)

    for idx, url in enumerate(urls, start=1):
        print(f"[{idx}/{total}] {url}")
        fetch_and_save_to_db(DB_PATH, url)

    print("✅ Done")
