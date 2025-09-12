# -*- coding: utf-8 -*-
import os
import sqlite3
from pathlib import Path

DB_PATH = Path('core') / 'database' / 'data.db'

def main() -> None:
    print('DB path:', DB_PATH)
    if not DB_PATH.exists():
        print('DB not found')
        return
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        print('Tables:', tables)
        for t in tables:
            try:
                cur.execute(f'SELECT * FROM {t} LIMIT 5')
                rows = cur.fetchall()
                print(f'--- {t} ---')
                if rows:
                    # Print columns header once
                    cols = rows[0].keys()
                    print('COLUMNS:', list(cols))
                for r in rows:
                    print(dict(r))
            except Exception as e:
                print('ERR', t, e)
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == '__main__':
    main()
