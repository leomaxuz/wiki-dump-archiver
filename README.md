# wiki-dump-archiver

Simple Python tool to:
- Download Wikimedia shorturls dump
- Extract URLs
- Fetch and archive page content into a local SQLite database

✅ Dumps can be downloaded from:  
https://dumps.wikimedia.org/other/shorturls/

---

## 🚀 Features
- Automatic download of `.gz` dump if not present locally
- Extract URLs from dump
- Fetch page HTML content
- Detect changes using SHA-256 hash
- Save pages to a local SQLite database (`data/wiki_pages.db`)

---

## ⚙️ Installation
```bash
git clone https://github.com/leomaxuz/wiki-dump-archiver.git
cd wiki-dump-archiver
pip install -r requirements.txt
```

---

⚙️ Configuration
In get.py you can set the dump URL and local file path:
```bash
# === CONFIGURATION ===
# Set dump URL and local file path here
DUMP_URL = 'https://dumps.wikimedia.org/other/shorturls/shorturls-20250728.gz'
GZ_FILE = 'data/dumps/shorturls-20250728.gz'
# =====================
```

---

## 📌 Usage
SQLite database: data/wiki_pages.db
Original dump file: data/dumps/

---

## 💡 Idea
This project helps to keep an offline mirror of selected Wikimedia pages
by regularly archiving them.

---

## ☕ Donate
If you find this project useful, you can support:

UCDT TRC20 wallet: TLkDJb4w188m5kNzGeKD97XGEfpfxrxUye

---

## 📬 Contact
Questions, suggestions, or want similar scripts?
📧 Email: uzbtube@gmail.com

---
