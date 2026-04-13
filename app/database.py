import sqlite3
from flask import g

DB_PATH = "FIT-TPMS.db"

def get_db():
    if 'db' not in g:
        # Tăng timeout lên 30s để đợi lock được giải phóng
        g.db = sqlite3.connect(DB_PATH, timeout=30)
        g.db.row_factory = sqlite3.Row
        
        try:
            # Chỉ cố gắng kích hoạt WAL mode và Foreign Keys, nếu không được (do bị khóa bởi tool khác) thì bỏ qua
            g.db.execute("PRAGMA journal_mode=WAL")
            g.db.execute("PRAGMA foreign_keys=ON")
        except sqlite3.OperationalError:
            # Nếu database bị khóa bởi chương trình khác (như DB Browser), bỏ qua cấu hình này
            pass
        
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()