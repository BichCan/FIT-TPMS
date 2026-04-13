import sqlite3

db_path = r'd:\FIT-TPMS\FIT-TPMS\FIT-TPMS.db'

def migrate():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Migrating 'registrations' table...")
    
    try:
        # Add knowledge column
        cursor.execute("ALTER TABLE registrations ADD COLUMN knowledge TEXT")
        print("Added 'knowledge' column.")
    except sqlite3.OperationalError:
        print("'knowledge' column already exists.")
        
    try:
        # Add project column
        cursor.execute("ALTER TABLE registrations ADD COLUMN project TEXT")
        print("Added 'project' column.")
    except sqlite3.OperationalError:
        print("'project' column already exists.")
        
    try:
        # Add topic column
        cursor.execute("ALTER TABLE registrations ADD COLUMN topic TEXT")
        print("Added 'topic' column.")
    except sqlite3.OperationalError:
        print("'topic' column already exists.")
        
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
