import sqlite3
import os

def run_migration():
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Try adding columns. Catch exceptions if they already exist.
    columns_to_add = [
        ("full_name", "TEXT"),
        ("phone", "TEXT"),
        ("linkedin_url", "TEXT"),
        ("bio", "TEXT")
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Column {col_name} already exists.")
            else:
                print(f"Error adding {col_name}: {e}")
                
    conn.commit()
    conn.close()
    print("Migration finished.")

if __name__ == '__main__':
    run_migration()
