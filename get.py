import gzip
import requests
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import hashlib

DB_PATH = 'data/wiki_pages.db'
DUMP_URL = 'https://dumps.wikimedia.org/other/shorturls/shorturls-20250728.gz'
GZ_FILE = 'data/dumps/shorturls-20250728.gz'

def init_db(db_path):
    # Create database and table if it doesn't exist
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
    # Download the dump file if it doesn't exist locally
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
    # Extract URLs from the gzip file
    urls = []
    with gzip.open(gz_file, 'rt', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parts = line.strip().split('|', 1)
            if len(parts) == 2:
                urls.append(parts[1])
    print(f"🔍 Found: {len(urls)} URLs")
    return urls

def save_urls_to_db(db_path, urls):
    # Save new URLs to the database; skip existing ones
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    total = len(urls)
    added = 0

    for idx, url in enumerate(urls, start=1):
        c.execute('SELECT 1 FROM pages WHERE url=?', (url,))
        if c.fetchone() is None:
            c.execute('INSERT INTO pages (url, content, hash, updated_at) VALUES (?, NULL, NULL, NULL)', (url,))
            added += 1
        # Show progress: [123/24545] Newly added: 10
        print(f"\r[{idx}/{total}] Newly added: {added}", end='', flush=True)

    conn.commit()
    conn.close()
    print()  # Newline at the end

def compute_hash(text):
    # Calculate SHA-256 hash of the text
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def fetch_missing_pages(db_path):
    # Fetch pages where content is still NULL and update them
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT url FROM pages WHERE content IS NULL')
    rows = c.fetchall()
    total = len(rows)

    success = 0

    for idx, (url,) in enumerate(rows, start=1):
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            content = r.text
            page_hash = compute_hash(content)
            now = datetime.now(timezone.utc).isoformat()

            c.execute('UPDATE pages SET content=?, hash=?, updated_at=? WHERE url=?',
                      (content, page_hash, now, url))
            success += 1
        except Exception:
            # If request fails, leave content as NULL to retry next time
            pass

        # Show progress: [123/24545] Fetched: 57
        print(f"\r[{idx}/{total}] Fetched: {success}", end='', flush=True)

    conn.commit()
    conn.close()
    print()  # Newline at the end

if __name__ == "__main__":
    init_db(DB_PATH)
    download_dump(DUMP_URL, GZ_FILE)

    urls = extract_urls_from_gz(GZ_FILE)
    save_urls_to_db(DB_PATH, urls)

    print("📄 Loading contents...")
    fetch_missing_pages(DB_PATH)

    print("✅ Done")
