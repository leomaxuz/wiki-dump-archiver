import gzip
import requests
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

DB_PATH = 'data/wiki_pages.db'
DUMP_URL = 'https://dumps.wikimedia.org/other/shorturls/shorturls-20250728.gz'
GZ_FILE = 'data/dumps/shorturls-20250728.gz'

def init_db(db_path):
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
    urls = []
    with gzip.open(gz_file, 'rt', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parts = line.strip().split('|', 1)
            if len(parts) == 2:
                urls.append(parts[1])
    print(f"🔍 Found: {len(urls)} URLs")
    return urls

def save_urls_to_db(db_path, urls):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    total, added = len(urls), 0

    for idx, url in enumerate(urls, start=1):
        c.execute('SELECT 1 FROM pages WHERE url=?', (url,))
        if c.fetchone() is None:
            c.execute('INSERT INTO pages (url, content, hash, updated_at) VALUES (?, NULL, NULL, NULL)', (url,))
            added += 1
        print(f"\r[{idx}/{total}] Newly added: {added}", end='', flush=True)

    conn.commit()
    conn.close()
    print()

def compute_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def fetch_and_update(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        content = r.text
        page_hash = compute_hash(content)
        now = datetime.now(timezone.utc).isoformat()

        # Har bir thread o‘z ulanishida yangilaydi
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('UPDATE pages SET content=?, hash=?, updated_at=? WHERE url=?',
                  (content, page_hash, now, url))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def fetch_missing_pages_parallel(db_path, max_workers=10):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT url FROM pages WHERE content IS NULL')
    rows = c.fetchall()
    conn.close()

    total = len(rows)
    success = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fetch_and_update, url[0]) for url in rows]
        for idx, future in enumerate(as_completed(futures), start=1):
            if future.result():
                success += 1
            print(f"\r[{idx}/{total}] Fetched: {success}", end='', flush=True)
    print()

if __name__ == "__main__":
    init_db(DB_PATH)
    download_dump(DUMP_URL, GZ_FILE)

    urls = extract_urls_from_gz(GZ_FILE)
    save_urls_to_db(DB_PATH, urls)

    print("📄 Loading contents...")
    fetch_missing_pages_parallel(DB_PATH, max_workers=10)

    print("✅ Done")
